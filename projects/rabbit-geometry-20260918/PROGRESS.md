# 進捗 / 再開ポイント

## 2026-09-19 セッション開始照合
開始時リモートmain `18a05d7d2de20618c9002db243340fd685f37089` のCHATGPT_JOB_PROMPT/README/EXECUTION_CONTRACT/tools/schema/v2サンプル/RESUME/INPUTS/runtime説明と作品指示を確認。再帰tree内に適用AGENTS.mdは検出されなかった。GitHub接続でread/write権限を確認。shell cloneとraw/API DNSは失敗。接続のGit Data APIおよびActions artifact downloadは実際に利用可能。dispatch専用操作はなく、現在のworkflowのmain job.json/review JSON push起動を利用する。

旧メモの『form-v002未投入』は古い。実際にはform-v002の全3工程と公開が終了済み。重複実行していない。実画像レビューを `reviews/form-v002.md/.json` に保存し、造形修正要求とした。ユーザーの今回の指定も造形のみ、テクスチャ等は別セッション。

## 最新の有効な制作保存地点
job `form-v002` / source `0fdebb95a32118f8bfa2e75da4ee0ecb2de23170`
Actions https://github.com/dekaazarashi1111-web/chatgpt-blender-bridge/actions/runs/35390326287
Release tag `creative-rabbit-geometry-20260918-form-v002-35390326287-1-3`
archive SHA256 `93dbd6936c126531da994e2ac3905af380b84f362275e5064f33d4ebf6cdb123`
manifest SHA256 `d61ae5dce72b2b3480183cc76a8387ede3804026d3ec91ec18c2a1bb5c89f1b1`
再開source_blend `workspace/resume/output/model/model.blend`
モデルSHA256 `f028acd02a8dd1ddd57f64d260e75fb50382151c72668cb1ea0fec39bc8f1f4f`

## 今行うこと
form-v003を準備し、v002から顔のC字顎・眼窩の丸い縁・耳の溝と丸い端部・掌につながる指・丸い爪先を修正する。現在このメモ時点でv003は未投入。必ず最新state/Actionsを再確認する。スクリプトと入力を先にcommitし、job.jsonは最後に追加。実行後は版を固定した画像レビューとRelease読戻しまで行う。完成と未確認を区別する。

## 過去
form-v001の記録と失敗方法はreviews/form-v001.mdに保存。過去の成功を次版に持ち越さない。未変更ジョイントなどは保持し、不要な工程の再実行は避ける。
