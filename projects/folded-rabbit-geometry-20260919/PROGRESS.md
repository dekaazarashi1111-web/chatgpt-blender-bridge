# 進捗 / folded-rabbit-geometry-20260919

対象は折れ耳・腕を下ろしたオリジナルキャラクター。今回も造形のみ。テクスチャ、UV仕上げ、リグは別セッション。旧rabbit-geometry-20260918/T-poseやstudio-smokeとは別作品。

## 実行中 — form-v005
source `464b693576b7ef291ab475149d3b9932e2014359`。
Actions https://github.com/dekaazarashi1111-web/chatgpt-blender-bridge/actions/runs/35437918879 attempt1。2026-09-19 10:37 UTC、pushによるCreative workspace起動/in_progressを実確認。実行直前のin_progress/queued一覧はともに空で、重複投入していない。
ソース保存commit `43478916527fadc952a6d3da623b1c3f19f1299d` の後でjob.jsonを追加。総予算18000秒、model/render/packageの3工程。対象版のBlender造形、保存、実画像合格はまだ未確認。

v004原寸比較の欠点を直す版。頭部を断面loftではなく連続したimplicit fieldから作り、狭い左右口元と鼻梁、下側だけの小さい中央溝、曲線的な頬カバー、丸い小鼻、眼球の収まりを調整。肩カバーと上腕外装を連続した曲面へ統合。指の狭い中間制御点を除き、指先を少しずらす。胴、骨盤、下腿、足、尾、蝶ネクタイ、折れ耳は再制作せずfingerprintで保持。
影響のない足detail/clay・耳detailの3画像はv004の実画像・hashと対象geometry fingerprintを確認して再利用。残る10画像を新しく描画し、全13ビューを納品する。Python構文検査とNumPy mesherの同解像度ローカル閉形状検査（1成分、watertight）は成功したが、Blender実行や視覚合格の代わりではない。

## 最新の実取得・検証済み保存地点 — form-v004
source `e67bb2848173b8c31f4b28e2b054999ed3c951de`。
Actions https://github.com/dekaazarashi1111-web/chatgpt-blender-bridge/actions/runs/35433907363 attempt1。実際は09:17 UTCに完走しており、前回の実行中表記は古かった。prepare/create成功、model/render/package全exit0、publication_errors=[]。
Release `creative-folded-rabbit-geometry-20260919-form-v004-35433907363-1-3`
- archive: 191794083 bytes / SHA256 `079b97150104e94be776e3396ae06b112f416a5680f8d45b919d4030ba4f3be2`
- manifest SHA256 `6dddb80268cde1edb1c508b228cc1314fc9c48b21b1295d1d6e0b6cb8a357184`
- 復元model: `workspace/resume/output/model/model.blend`、135385476 bytes / SHA256 `6f9c5d9fc58968a0b819b21b1239948b7f29db0ac424e313b9ff3f9878a16269`
- 納品model: `output/package/folded_rabbit_geometry.blend`、135390076 bytes / SHA256 `9ab637f33aafb8f6f751c752ed0047152f650477a81a446755e818304713175e`

host/review ZIPを実取得してAPI digestを照合。CIがReleaseから読戻したmanifest実バイトhashをstateと照合し、manifest全99ファイルのsize/hashを今回独立照合、欠落/不一致0。両CI再読込成功、外部依存欠落なし、全visible meshの非manifold/境界辺0、必須部品・口元group・有限座標・no image-texture node検査成功。13画像/フレーミング検証成功。
ただし実画像には広い板状の口元、頭頂の横段差、丸いボタン状の頬、指のくびれ、肩の接合が残るため完成ではない。reviews/form-v004.md/jsonへsource/archive固定のchanges_requestedを保存（commit ef8543cd3090b6f9d67a81d0c7808bd8430f05c4）。レビュー適用結果はworkspace-stateの実際の記録を読む。

## 以前の保存地点
form-v003: Release `creative-folded-rabbit-geometry-20260919-form-v003-35432676691-1-3`、archive `eab8cfd9b794382f18439f37dcbda061040f551052c6f6040537d71e845b9a3f`、manifest `45d3eab89f2912a10bcdb42038b4a017d9ffaaf76718480809c639191cad358e`。レビューはchanges_requested。v004が実復元済み。
form-v002: Release `creative-folded-rabbit-geometry-20260919-form-v002-35430997050-1-3`、archive `536ed187f54383979428459739169a9405394d76caf55476e5f74472306d5c4c`、manifest `2496607eb41d29ecc00d75a2f404c59f4c00d875df9ccb6cae0d368798663c47`。過去の詳細は各reviewsとGit履歴に保存。

## 次の作業
同じv005 Actionsとworkspace-stateを追跡。完了後にログ・manifest・実出力・再読込・形状監査・新規10画像と再利用3画像の証拠を確認し、原寸参照と比較する。実行成功だけでは完成としない。必要なら新IDで修正、対象source/archive固定レビューを保存・状態反映する。
失敗時はdocs/RESUME.mdに従い公開完了済み工程snapshotから再開。今回の変更に影響のない工程を繰り返さない。ローカルだけを保存済みと呼ばない。現時点の最終Release確認はCI読戻しmanifest・server digestとActions artifact実ファイルの照合であり、最終Release TARをこのセッションが再取得したという意味ではない。

## 原寸入力・実行経路
Libraryから元の1086x1448 PNG3枚を取得でき、INPUTS.mdの元画像SHA256とすべて一致した。原寸を今回の視覚比較に使用する。GitHub/Release/blendに保存済みの300x400 WebPは同じ画像の実画素派生であり代替生成画像ではない。各jobへ復元・持越し。原寸PNGそのものはGitHub未アップロードのまま。テクスチャ貼付けは行わない。
今回開始HEAD `9160fcd1aaa5fabec4cbc040e0d60750a42990d1` の実装/契約/ツール/schema/再開説明/レビュー実装を確認。再帰treeにAGENTS.md該当なし。shell gitとBlender/PyPI外部接続はDNS失敗。接続済みGitHub APIでmain非force更新とpushイベント起動が成功。既存の検証済みruntimeを継続し、不要な再buildはしていない。
