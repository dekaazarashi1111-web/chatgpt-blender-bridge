# 決定・実行経路

開始時のリモートmain HEAD: `9a79473561b9a38d2ecf4a40c224ad1e849f339a`。そのcommitの CHATGPT_JOB_PROMPT.md、README、EXECUTION_CONTRACT、tools.json、v2 schema、両studio-smokeサンプル、INPUTS/RESUME/runtime説明、現在のworkflow/runner/restore実装を確認。root、projects親、および今回変更する.github/workflowsのtreeに適用AGENTS.mdなし。

GitHub get_repo は push/maintain/admin=true。shell `git ls-remote https://github.com/dekaazarashi1111-web/chatgpt-blender-bridge.git refs/heads/main` は `Could not resolve host: github.com` で失敗。GitHub接続のGit Data API、mainへの非force ref更新、job.json追加のpush起動を使う。接続にはworkflow_dispatch専用操作を確認できておらず、dispatch成功とは呼ばない。既存runtime-v2の検証済みimageを再利用し、ビルドのやり直しをしない。

## 継承元の実状態
`folded-rabbit-geometry-20260919/form-v006`、source `a2c964a566719aaa8364947a1ecddf9c0a35165b`。
Actions https://github.com/dekaazarashi1111-web/chatgpt-blender-bridge/actions/runs/35439434026 はmodel/render/package全exit0。workspace-stateはneeds_review、finished_at 2026-09-19T11:20:37Z、publication_errors=[]。古いPROGRESSのrunning表記より実記録を優先する。2026-09-21の照合時、repository全体のin_progress runは0件。
Release `creative-folded-rabbit-geometry-20260919-form-v006-35439434026-1-3`
archive SHA256 `29e9252abf66f7264d1386edfa8b8b6db290a5f345014eaa513dac04864318b7`
manifest SHA256 `31ad5a6d25a1d0bdef78b32ead9185a2b846362c541f5c50af53696b9d865951`

通常resumeは同一project限定であることをbridge/artifacts.pyで確認。新IDへの継承は、既存form-v001/import_parent.pyと同じ明示的な同一repository内Release importを使う。元project/job/tagと両hashを検証する。通常resumeの同一project保護を弱めない。

## 画像とツール制約
今回の3画像はコンテナに元PNGとして提示された。外観・役割とbyte数は旧INPUTS記録と対応するが、このセッションで原寸PNGの独立hash計算はまだ成功していない。旧入力の実WebP3枚を同じGit blobから新projectへ保存し、入力hashを実行時に照合する。新たな生成代替画像を作らない。原寸PNGのGitHub保存完了とは扱わない。

v006のreview artifact10582919988 (259036685 bytes)とhost artifact10582964893をGitHub接続で取得したが、その後container.exec、Python、open_imageが繰返しTransportTimeoutErrorを返した。host ZIPの意図的再materializeは成功、review ZIPはmaterialize上限104857600 bytes超過と明示的に拒否された。今回のセッションがZIPの中身/画像/hashを独立確認したとはまだ言わない。GitHub側の読み戻しと小さい視覚専用artifactの経路を用意し、実画像の取得回復を試みる。

まず元の造形を改変せず、hash検証付きで新projectへ継承し、自己完結した保存地点と軽量プレビューを確保する。実画像を見ないまま顔を再変形して不確かな改悪を重ねない。このintakeは造形の完成判定でも新しい形状改良版でもない。
