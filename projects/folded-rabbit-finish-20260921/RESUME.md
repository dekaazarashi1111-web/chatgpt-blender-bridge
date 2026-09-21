# 会話履歴なしで造形仕上げを再開する

## 対象と最初の確認
対象は `folded-rabbit-finish-20260921`。短い外側折れ耳、腕を下ろした姿勢、欠損のない丸い外装のオリジナルキャラクター。BRIEF.md、DECISIONS.md、PROGRESS.md、reviews/intake-v001.mdを読む。テクスチャ/UV仕上げ/リグはこの工程の対象外。
main最新HEADのexecutorルールを再取得し、workspace-stateの本project/state.json、jobs/intake-v001.json、対応する実Actionsを照合する。保存時点でintake-v001は終了済みneeds_review。後続jobが実行中なら重複投入しない。

## 有効な同一project復元点
次の新IDのv2 jobの `resume` に使用する。既存intake-v001を再実行したり、cross-project resumeの保護を解除したりしない。

```json
{
  "release_tag": "creative-folded-rabbit-finish-20260921-intake-v001-35563023916-1-1",
  "project_id": "folded-rabbit-finish-20260921",
  "job_id": "intake-v001",
  "archive_sha256": "c5d41457ff3dbf988a6ac57b5ada016c0d020821be67c33024f1b80e81942bc2",
  "manifest_sha256": "50dc6458d91ef183ff68e20110674bf9f0e04bd262c61cbf3f560d1f3f511e4a"
}
```

Blender `source_blend`: `workspace/resume/output/intake/model/model.blend`
Blender scriptからの依存元: `Path(WORKSPACE_DIR) / 'resume' / 'output' / 'intake' / 'model'`
この.blendのSHA256は `aa98019f06ff34ea3d700981ad594947dbb55ac6379bcb22a4a2ab2980d03b08`、159212580 bytes。intakeは実バイトを変更していないので、sceneのproject_id/job_idは元の `folded-rabbit-geometry-20260919` / `form-v006` のまま。新規改訂時は、この旧identityとhashを照合した後で新project/jobのmetadataへ移す。新project identityだと仮定して旧assertをそのまま通してはいけない。

`geometry_source.py` はv006、`implicit.py`、`cheek.py`、それ以前の検証済みhelperソース、`reference_render_cache/` が同じmodelフォルダにある。元のmodel.pyを無変更で再実行するとv005親/hash/パスのassertに合わず、また不要な再造形になる。現在のmeshを読み込んで必要な修正だけ行う。復元依存は次のOUTPUT_DIRへコピー/packし、再帰的なresume全体の複製は避ける。

## まず見る実画像
Release内の `output/intake/visual/package/reference_comparison.jpg` と `geometry_contact_sheet.jpg` を開く。次に `output/intake/visual/render/` の以下を原寸で確認する。
front.png、right.png、back.png、three_quarter.png、front_uniform_clay.png、head_front.png、head_right.png、head_three_quarter.png、head_uniform_clay.png、ears_detail.png、hand_detail.png、feet_detail.png、feet_uniform_clay.png。

これらは実際のBlender出力をhash付きで継承した画像であり、このセッションが新規生成した画像ではない。13ビューの内訳は親v006のrender_manifestで確認する。intakeのpreview_count35はpackage/renderの重複コピー・参照・小画像も含むため、35個の独立ビューという意味ではない。
参照: `output/intake/references/front.webp`、side.webp、back.webp。同じ実画像からの300x400派生。元の3PNGは今回のチャットに添付されたがGitHub原寸保存は未了。詳細INPUTS.md。画像生成ツールによる代替画像を実レンダーや元参照に見立てない。

## 軽量artifact（期限付き）
実行 https://github.com/dekaazarashi1111-web/chatgpt-blender-bridge/actions/runs/35563023916
visual: artifact10621934842、13587953 bytes、SHA256 `64f35eae4b692abe12d6356e1bc0821f77c1b17c1063c1a6a5a6237a786bfa19`。
host: artifact10622368899、7230 bytes、SHA256 `6e1a9f986d8c911fd0a2354954ef0694d771bef8749791eb5b31628b6d7d3cae`。
full review: artifact10622423788、98900633 bytes、SHA256 `ff1ba07a8b7f8112843c289afbc92aecf6e721b4ba28ebdd779bbc528696fb1e`。
artifactは2026-10-21失効予定。永続保存地点は上のReleaseであり、artifactだけに依存しない。親の259 MB ZIPを再取得しなくても、本projectの軽量画像と同一project snapshotで続行できる。

## 技術記録
`output/intake/model/geometry_audit.json`、validation.json、lineage.json、head_geometry.json/npz、`output/intake/upstream_evidence/render/render_manifest.json`、validation.jsonと各ソースを確認する。親v006の実行は成功したが、今回のセッションでは実画像もこれらのZIP内JSON本文もローカルで開けていない。manifest上の存在/hash照合と本文を読むことを区別する。
CI読み戻しmanifestの保存先: workspace-state `workspaces/folded-rabbit-finish-20260921/evidence/intake-v001/latest-manifest.json`。

## 残作業と終了条件
画像表示/実行環境を回復し、実画像で形状を比較する。前版レビューの修正対象は板状口元、浮く花弁状頬、眼窩/口元のうねりであり、v006はそれを直すための未レビュー版。元の指示/原寸参照を優先し、改善済みと決めつけない。全身や手足など影響のない受入済み工程は再制作しない。確認できた不一致のみ新jobで修正し、版を固定した実画像レビュー、必要な再読込/検査、Release保存を終えてから完成判定する。
