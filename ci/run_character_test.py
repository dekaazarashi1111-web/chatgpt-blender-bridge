"""One-shot public-repository CI test, separate from the Oracle worker queue.
Never writes queue/status or claims an Oracle execution. Outputs are CI artifacts.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from bridge.jobs import load_job


def run(command, log, timeout):
    with log.open('a', encoding='utf-8') as stream:
        stream.write('COMMAND=' + ' '.join(command) + '\n')
        stream.flush()
        try:
            process = subprocess.run(command, cwd=ROOT, stdout=stream,
                stderr=subprocess.STDOUT, timeout=timeout, check=False)
            return process.returncode
        except subprocess.TimeoutExpired:
            stream.write('TIMEOUT\n')
            return 124


def main():
    descriptors = sorted((ROOT / 'queue/pending').glob('blue-animatronic-v*/job.json'))
    if not descriptors:
        raise RuntimeError('No blue animatronic job found')
    job, files = load_job(descriptors[-1])
    output = ROOT / 'ci_artifacts' / job['job_id']
    output.mkdir(parents=True, exist_ok=True)
    log = output / 'blender.log'
    blender = shutil.which('blender')
    if not blender:
        raise RuntimeError('Blender executable not found')
    command = [blender, '--background', '--factory-startup', '--disable-autoexec', '--threads', '2']
    if job.get('source_blend'):
        command.append(str(ROOT / job['source_blend']))
    command += ['--python-exit-code', '1', '--python', str(ROOT / 'bridge/blender_entry.py'),
        '--', '--job', str(files.descriptor), '--script', str(files.script), '--run-dir', str(output)]
    code = run(command, log, min(job['timeout_seconds'], 1500))
    blend = output / 'output/model.blend'
    validate_code = None
    if code == 0 and blend.is_file():
        validate_code = run([blender, '--background', '--disable-autoexec', str(blend),
            '--python-exit-code', '1', '--python', str(ROOT / 'bridge/blender_validate.py'),
            '--', '--report', str(output / 'validation.json')], log, 240)
    validation = json.loads((output/'validation.json').read_text()) if (output/'validation.json').is_file() else {}
    checks = {'script_exit': code == 0, 'blend_exists': blend.is_file() and blend.stat().st_size > 0,
        'reopen_ok': validate_code == 0 and validation.get('pass') is True,
        'report_exists': (output/'blender_report.json').is_file()}
    for view in job['preview']['views']:
        path = output/'previews'/f'{view}.png'
        checks['preview:' + view] = path.is_file() and path.stat().st_size > 0
    artifacts = {}
    for path in sorted(output.rglob('*')):
        if path.is_file():
            artifacts[path.relative_to(output).as_posix()] = {'bytes': path.stat().st_size,
                'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    criteria = []
    for criterion in job['acceptance_criteria']:
        status = ('pass' if checks.get(criterion['check'], False) else 'fail') if criterion['kind'] == 'automatic' else 'pending_review'
        criteria.append({**criterion, 'status': status})
    report = {'schema_version': 1, 'job_id': job['job_id'],
        'execution_backend': 'github-hosted-runner-not-oracle',
        'state': 'needs_review' if all(checks.values()) else 'failed',
        'commit': os.environ.get('GITHUB_SHA'), 'workflow_run_id': os.environ.get('GITHUB_RUN_ID'),
        'actor': os.environ.get('GITHUB_ACTOR'),
        'finished_at': datetime.now(timezone.utc).isoformat(),
        'blender_exit_code': code, 'validation_exit_code': validate_code,
        'blender_version': subprocess.check_output([blender, '--version'], text=True).splitlines()[0],
        'checks': checks, 'acceptance_criteria': criteria, 'artifacts': artifacts}
    (output/'ci_manifest.json').write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    shutil.copy2(files.script, output/'build_script.py')
    shutil.copy2(files.descriptor, output/'job.json')
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(log.read_text(encoding='utf-8')[-16000:])
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a', encoding='utf-8') as stream:
            stream.write('# Blender character test\n\nBackend: GitHub-hosted runner, not Oracle.\n\n')
            stream.write('```json\n'+json.dumps(report, indent=2)+'\n```\n')
    return 0 if all(checks.values()) else 1


if __name__ == '__main__':
    raise SystemExit(main())
