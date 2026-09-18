# 決定事項

- 新規IDで開始。別作品の生成済み.blendや品質合格をそのまま今回の完成品にしない。
- 開始HEADのCHATGPT_JOB_PROMPT、README、EXECUTION_CONTRACT、tools.json、v2 schema、2つのstudio-smoke job、docs/INPUTS、docs/RESUME、runtime/README、実装tool_entry/blender_entry/workflowを確認。rootおよびprojectsに適用AGENTS.mdなし。
- GitHub接続にはGit Data APIのblob/tree/commit/ref、contents書き込み、Actions状態・ログ・artifact取得がある。dispatch専用操作は見つからないため既存main push triggerで投入する。
- 実際のshell `git clone https://github.com/dekaazarashi1111-web/chatgpt-blender-bridge.git` は `Could not resolve host: github.com` で失敗。接続APIで作業を続ける。これはconnectorの書き込み不可を意味しない。
- `/actions/workflows/creative-job.yml/runs?...` はfetchのURL検査で400。`/actions/runs?status=in_progress` は成功し開始時0件。新作品のworkspace-stateパスは404（未作成）。
- 既存技術記録でこのUbuntu BlenderはOpenImageDenoiserなしと判明。Cycles denoising=Falseを使い、不要なruntime再ビルドはしない。各実行の実バージョンとimage digestはrunner証拠から確認する。
- 参考の艶消し感、暗い目、口吻と顎の連続性を優先。安易な白球の目、大きな金属肩球、球を並べただけの口吻、四角い破れ、白すぎる腹部を避ける。
