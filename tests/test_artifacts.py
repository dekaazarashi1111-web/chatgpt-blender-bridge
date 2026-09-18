from __future__ import annotations

import copy
import hashlib
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
import urllib.error
import urllib.parse
from unittest.mock import Mock, patch

import bridge.artifacts as artifacts
from bridge.artifacts import (
    ARCHIVE_NAME, MANIFEST_NAME, ArtifactError, GitHubReleases,
    create_snapshot, extract_snapshot, publish_snapshot, restore_snapshot,
)
from bridge.state import sha256_file


REPOSITORY = "example/creative"
IDENTITY = dict(repository=REPOSITORY, project_id="project-one", job_id="job-one", run_id="123", attempt=1, sequence=2)


class FakeGitHub:
    """HTTP transport simulation: exercise real client request and digest code."""
    def __init__(self):
        self.calls = []
        self.assets = {}
        self.release = None
        self.omit_digest = False
        self.wrong_digest = False

    def open(self, request, timeout):
        self.calls.append(request)
        method, parsed = request.get_method(), urllib.parse.urlparse(request.full_url)
        if method == "POST" and parsed.hostname == "api.github.com":
            if self.release is not None:
                raise urllib.error.HTTPError(request.full_url, 422, "already exists", {}, None)
            self.release = {"id": 11, **json.loads(request.data), "assets": []}
            return io.BytesIO(json.dumps(self.release).encode())
        if method == "POST" and parsed.hostname == "uploads.github.com":
            content = request.data.read()
            name = urllib.parse.parse_qs(parsed.query)["name"][0]
            asset_id = 20 + len(self.assets)
            self.assets[asset_id] = content
            asset = {"id": asset_id, "name": name, "size": len(content), "state": "uploaded"}
            if not self.omit_digest:
                asset["digest"] = "sha256:" + ("0" * 64 if self.wrong_digest else hashlib.sha256(content).hexdigest())
            self.release["assets"].append(asset)
            return io.BytesIO(json.dumps(asset).encode())
        if method == "PATCH":
            self.release.update(json.loads(request.data))
            return io.BytesIO(json.dumps(self.release).encode())
        if "/releases/assets/" in parsed.path:
            return io.BytesIO(self.assets[int(parsed.path.rsplit("/", 1)[1])])
        if "/releases/tags/" in parsed.path:
            return io.BytesIO(json.dumps(self.release).encode())
        raise AssertionError("Unexpected fake HTTP request")


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.source = self.root / "source"
        (self.source / "output").mkdir(parents=True)
        (self.source / "output" / "model.blend").write_bytes(b"BLENDER-test-payload")
        (self.source / "output" / "材質.png").write_bytes(b"texture")
        (self.source / "checkpoint.json").write_text('{"stage":"materials"}')

    def tearDown(self):
        self.temporary.cleanup()

    def snapshot(self):
        return create_snapshot(self.source, self.root / "snapshot", **IDENTITY)

    def extract(self, archive, manifest, **extra):
        return extract_snapshot(archive, self.root / "restored", manifest,
                                repository=REPOSITORY, project_id=IDENTITY["project_id"],
                                job_id=IDENTITY["job_id"], tag=manifest["release_tag"],
                                archive_sha256=manifest["archive"]["sha256"], **extra)

    def test_snapshot_roundtrip_unicode_and_binary_data(self):
        archive, _, manifest = self.snapshot()
        self.extract(archive, manifest)
        for source in self.source.rglob("*"):
            if source.is_file():
                self.assertEqual(source.read_bytes(), (self.root / "restored" / source.relative_to(self.source)).read_bytes())
        self.assertEqual(manifest["file_count"], 3)
        self.assertEqual(manifest["archive"]["sha256"], sha256_file(archive))

    def test_reject_symlink_and_archive_inside_source(self):
        (self.source / "secret").symlink_to(self.root / "outside")
        with self.assertRaises(ArtifactError):
            self.snapshot()
        (self.source / "secret").unlink()
        with self.assertRaises(ArtifactError):
            create_snapshot(self.source, self.source / "archive", **IDENTITY)

    def test_reject_symlink_ancestor_and_ancestor_swap_during_archive(self):
        alias = self.root / "alias"
        alias.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(ArtifactError):
            create_snapshot(alias / "source", self.root / "static", **IDENTITY)
        original_list = artifacts._list_files

        def swap_after_list(root, maximum, excluded):
            result = original_list(root, maximum, excluded)
            moved = self.root / "moved"
            self.source.rename(moved)
            self.source.symlink_to(moved, target_is_directory=True)
            return result

        with patch("bridge.artifacts._list_files", side_effect=swap_after_list):
            with self.assertRaises(ArtifactError):
                self.snapshot()
        self.assertFalse((self.root / "snapshot" / ARCHIVE_NAME).exists())

    def test_final_snapshot_omits_only_named_top_level_directories(self):
        for path in (self.source / "checkpoints", self.source / "resume", self.source / "output" / "checkpoints"):
            path.mkdir(parents=True)
            (path / "copy.blend").write_bytes(b"old")
        _, _, manifest = create_snapshot(self.source, self.root / "trimmed", **IDENTITY,
                                         exclude_top_level=("checkpoints", "resume"))
        paths = {entry["path"] for entry in manifest["files"]}
        self.assertIn("output/checkpoints/copy.blend", paths)
        self.assertNotIn("resume/copy.blend", paths)
        self.assertNotIn("checkpoints/copy.blend", paths)
        self.assertEqual(manifest["excluded_top_level"], ["checkpoints", "resume"])

    def test_quotas_stop_snapshot_and_restore(self):
        with self.assertRaises(ArtifactError):
            create_snapshot(self.source, self.root / "small", **IDENTITY, max_unpacked_bytes=1)
        with self.assertRaises(ArtifactError):
            create_snapshot(self.source, self.root / "few", **IDENTITY, max_files=1)
        with self.assertRaises(ArtifactError):
            create_snapshot(self.source, self.root / "compressed", **IDENTITY, max_archive_bytes=10)
        archive, _, manifest = self.snapshot()
        with self.assertRaises(ArtifactError):
            self.extract(archive, manifest, max_unpacked_bytes=1)
        self.assertFalse((self.root / "restored").exists())

    def test_corruption_and_existing_destination_leave_workspace_untouched(self):
        archive, _, manifest = self.snapshot()
        archive.write_bytes(archive.read_bytes() + b"tampered")
        with self.assertRaises(ArtifactError):
            self.extract(archive, manifest)
        archive, _, manifest = self.snapshot()
        (self.root / "restored").mkdir()
        (self.root / "restored" / "keep").write_text("original")
        with self.assertRaises(ArtifactError):
            self.extract(archive, manifest)
        self.assertEqual((self.root / "restored" / "keep").read_text(), "original")

    def test_reject_path_traversal_links_sparse_and_huge_tar_metadata(self):
        _, _, original = self.snapshot()
        cases = [("../escaped", tarfile.REGTYPE, 1),
                 ("output/model.blend", tarfile.SYMTYPE, 0),
                 ("output/model.blend", tarfile.LNKTYPE, 0),
                 ("output/model.blend", tarfile.GNUTYPE_SPARSE, 0),
                 ("metadata", tarfile.XHDTYPE, 8193)]
        for name, kind, size in cases:
            with self.subTest(name=name, kind=kind):
                archive = self.root / "bad.tar.gz"
                with tarfile.open(archive, "w:gz") as stream:
                    item = tarfile.TarInfo(name)
                    item.type, item.size, item.linkname = kind, size, "/etc/passwd"
                    stream.addfile(item, io.BytesIO(b"x" * size))
                manifest = copy.deepcopy(original)
                manifest["archive"].update(bytes=archive.stat().st_size, sha256=sha256_file(archive))
                with self.assertRaises(ArtifactError):
                    self.extract(archive, manifest)
                self.assertFalse((self.root / "escaped").exists())
                self.assertFalse((self.root / "restored").exists())

    def test_manifest_identity_and_hashes_are_checked(self):
        archive, _, original = self.snapshot()
        for key, value in (("repository", "other/repo"), ("project_id", "other"), ("job_id", "other")):
            manifest = copy.deepcopy(original)
            manifest[key] = value
            with self.assertRaises(ArtifactError):
                self.extract(archive, manifest)
        manifest = copy.deepcopy(original)
        manifest["files"][0]["sha256"] = "0" * 64
        with self.assertRaises(ArtifactError):
            self.extract(archive, manifest)
        self.assertFalse((self.root / "restored").exists())

    def test_publish_verify_restore_via_http(self):
        fake = FakeGitHub()
        client = GitHubReleases(REPOSITORY, "private-token", opener=fake)
        record = publish_snapshot(self.source, output_dir=self.root / "published", client=client, **IDENTITY)
        self.assertFalse(fake.release["draft"])
        self.assertEqual(record["release_tag"], "creative-project-one-job-one-123-1-2")
        # Display URLs are never consumed for downloads: repository and IDs own routing.
        record["archive_url"] = "https://attacker.invalid/steal"
        restored = restore_snapshot(record, self.root / "restored", repository=REPOSITORY,
                                    project_id=IDENTITY["project_id"], client=client)
        self.assertEqual(restored["file_count"], 3)
        self.assertEqual((self.root / "restored" / "output" / "model.blend").read_bytes(), b"BLENDER-test-payload")
        self.assertTrue(all("attacker.invalid" not in req.full_url for req in fake.calls))
        with self.assertRaises(ArtifactError):
            publish_snapshot(self.source, output_dir=self.root / "duplicate", client=client, **IDENTITY)

    def test_upload_verification_failure_never_publishes_release(self):
        fake = FakeGitHub()
        fake.wrong_digest = True
        with self.assertRaises(ArtifactError):
            publish_snapshot(self.source, output_dir=self.root / "published",
                             client=GitHubReleases(REPOSITORY, "token", opener=fake), **IDENTITY)
        self.assertTrue(fake.release["draft"])
        self.assertFalse(any(req.get_method() == "PATCH" for req in fake.calls))

    def test_missing_api_digest_uses_download_verification(self):
        fake = FakeGitHub()
        fake.omit_digest = True
        publish_snapshot(self.source, output_dir=self.root / "published",
                         client=GitHubReleases(REPOSITORY, "token", opener=fake), **IDENTITY)
        self.assertEqual(sum("/releases/assets/" in req.full_url for req in fake.calls), 2)

    def test_restore_rejects_wrong_project_and_modified_remote_manifest(self):
        fake = FakeGitHub()
        client = GitHubReleases(REPOSITORY, "token", opener=fake)
        record = publish_snapshot(self.source, output_dir=self.root / "published", client=client, **IDENTITY)
        with self.assertRaises(ArtifactError):
            restore_snapshot(record, self.root / "restored", repository=REPOSITORY, project_id="different", client=client)
        fake.assets[record["manifest_asset_id"]] += b" "
        with self.assertRaises(ArtifactError):
            restore_snapshot(record, self.root / "restored", repository=REPOSITORY, project_id=IDENTITY["project_id"], client=client)
        self.assertFalse((self.root / "restored").exists())

    def test_download_redirect_strips_token_and_rejects_foreign_host(self):
        blob = b"file"
        opener = Mock()
        opener.open.side_effect = [urllib.error.HTTPError("https://api.github.com", 302, "redirect",
                                   {"Location": "https://release-assets.githubusercontent.com/signed?signature=abc"}, None),
                                   io.BytesIO(blob)]
        client = GitHubReleases(REPOSITORY, "secret", opener=opener)
        client.download(12, self.root / "download", max_bytes=100, expected_sha256=hashlib.sha256(blob).hexdigest())
        first, second = [call.args[0] for call in opener.open.call_args_list]
        self.assertEqual(first.get_header("Authorization"), "Bearer secret")
        self.assertIsNone(second.get_header("Authorization"))
        opener.open.side_effect = [urllib.error.HTTPError("https://api.github.com", 302, "redirect", {"Location": "https://evil.invalid/"}, None)]
        with self.assertRaises(ArtifactError):
            client.download(12, self.root / "download", max_bytes=100, expected_sha256=hashlib.sha256(blob).hexdigest())


if __name__ == "__main__":
    unittest.main()
