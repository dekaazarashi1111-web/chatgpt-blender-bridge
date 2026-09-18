# 進捗と再開入口

## 現在の作業
`build-v001` を投入し、Actions が実行中であることを確認した。重複投入しない。

- Project: `worn-violet-rabbit-20260918`
- Job descriptor: `projects/worn-violet-rabbit-20260918/jobs/build-v001/job.json`
- Source commit: `397cbc69c21c323727da2e3e6163ce23586d357d`
- Actions run: https://github.com/dekaazarashi1111-web/chatgpt-blender-bridge/actions/runs/35364229702
- Actions create job ID: `105662681961`
- Runtime: `ghcr.io/dekaazarashi1111-web/chatgpt-creative-runtime@sha256:2d4029b9359dcac82a21e726787fa6df0f1d35504d2bcdf1f8506031b62fa8b9`
- Runner started: `2026-09-18T15:44:44.113706Z`
- Descriptor/source validation Actions succeeded: https://github.com/dekaazarashi1111-web/chatgpt-blender-bridge/actions/runs/35364229489

## 現時点で確認した内容
実際のユーザー画像の圧縮参照版が GitHub の inputs/reference.webp に保存され、ジョブのSHA検査を通って選択された。4本の制作ソースが定義より先にcommitされた。2K材質生成はローカルでも実行して画像を開いた。Blender本体の保存・外観の最終合格はまだ確認していない。

## 継続時は必ず実状態を読み直す
この文書の実行中表示よりも、以下の最新実行記録を優先する。
- workspace-state: `workspaces/worn-violet-rabbit-20260918/state.json`
- per-job: `workspaces/worn-violet-rabbit-20260918/jobs/build-v001.json`
- 上記 Actions のstatus/logs
- latest_snapshot / step_snapshots に対応するRelease manifestとarchive

実行中なら追跡し、同一内容を再投入しない。失敗・中断なら docs/RESUME.md に従って有効なsnapshotを検証し、別job IDから再開する。完了なら `creative-review-worn-violet-rabbit-20260918-0-35364229702-1` artifactをダウンロードし、package/three_view.png, comparison.png, details.pngと各実レンダーを開く。Releaseを永続保存の正本とする。

## 未完了
実モデルと保存ファイルの検証、参考画像との実レンダー比較、必要な造形・質感修正、対象版にpinしたレビュー、最終成果物リンクと引継ぎ記録。実行成功だけでapprovedにしない。
