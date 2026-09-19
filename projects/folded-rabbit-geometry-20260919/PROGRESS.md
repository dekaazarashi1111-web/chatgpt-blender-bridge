# 進捗 / folded-rabbit-geometry-20260919

対象は今回添付の折れ耳・腕を下ろしたオリジナルキャラクター。造形のみ。テクスチャ、UV仕上げ、リグは別セッション。旧rabbit-geometry-20260918/T-poseやstudio-smokeと混同しない。

## 実行中 — form-v004
source `e67bb2848173b8c31f4b28e2b054999ed3c951de`。
Actions https://github.com/dekaazarashi1111-web/chatgpt-blender-bridge/actions/runs/35433907363 attempt1。2026-09-19 09:09 UTC、push起動を実確認。prepareのレビュー適用/選択は成功、createがin_progress。重複投入しない。
スクリプト・復元依存を先に用意しjob.jsonを最後に追加。総予算18000秒、model/render/packageの3工程。対象版の造形成功・画像合格はまだ未確認。

v003の実画像比較で、前方へ張り出す頬、連続した鼻梁/口元、眼球の深さ、上の前歯2本の控えめな露出、丸い下歯列、ヒゲの軌道、連続して曲がる指、骨盤の段差、耳溝の薄い縁、爪先の丸い角形を修正。頭部は単一メッシュの滑らかな変形場で作り、左右口元のvertex groupを保存。受入済み親import、胴、下腿、尻尾、蝶ネクタイ、折れ耳上部は再構築せずfingerprint保持。寸法は回転bounding boxでなく実メッシュ頂点から検査する。

## 最新の実取得・検証済み保存地点 — form-v003
source `c89554674a7ed6a55bcb6a2d0ecefb8ffcb7711f`。
Actions https://github.com/dekaazarashi1111-web/chatgpt-blender-bridge/actions/runs/35432676691 attempt1、全工程exit0、prepare/create成功、publication_errorsなし。
Release `creative-folded-rabbit-geometry-20260919-form-v003-35432676691-1-3`
- archive: 172080545 bytes / SHA256 `eab8cfd9b794382f18439f37dcbda061040f551052c6f6040537d71e845b9a3f`
- manifest: 17055 bytes / SHA256 `45d3eab89f2912a10bcdb42038b4a017d9ffaaf76718480809c639191cad358e`
- 復元model: `workspace/resume/output/model/model.blend`、125810148 bytes / SHA256 `7d3ca0c79a149f1377392b071444b4adbe8f94e2d71af4a2cfef3e5fa682f1bb`
- 納品model: `output/package/folded_rabbit_geometry.blend`、125814748 bytes / SHA256 `20475c878ca0188f882cf606d396b025abc6dcb5948fb633b965bc4ef35a3dc7`

host/review ZIPを実取得、API digest、Release読戻しmanifest実バイトhash、全96出力size/hashを独立照合し欠落/不一致0。両再読込成功、外部依存欠落なし、全visible meshの非manifold/境界辺0、必要部品・口元group・有限座標・no image-texture node検査成功。13画像/フレーミング検証済み。
実画像を開いた結果、まだ形状不一致があるため完成とはしない。reviews/form-v003.md/jsonに対象source/archive固定のchanges_requestedを保存した。v002もreviews/form-v002.md/jsonに検証と不合格理由を保存。v004 prepareのレビュー適用成功を実確認。

## さらに前の保存地点 — form-v002
Release `creative-folded-rabbit-geometry-20260919-form-v002-35430997050-1-3`。
archive SHA256 `536ed187f54383979428459739169a9405394d76caf55476e5f74472306d5c4c`、manifest SHA256 `2496607eb41d29ecc00d75a2f404c59f4c00d875df9ccb6cae0d368798663c47`。
復元blend SHA256 `adbb099ed8f76fc69a6c309064ad82b04c472c6e8d8457a3b4be49b73374d3f3`。全93ファイル照合済み。v003はこのarchiveをrunnerで復元/hash検証した。

## 次の作業
同じv004 Actionsとworkspace-stateを追跡。終了後にログ・manifest・実出力・再読込・形状監査・13全体/クレイ/詳細画像を確認して原寸参照と比較する。未確認を確認済みと書かない。必要なら新IDで修正し、最終対象版のレビュー・状態反映・保存地点を記録する。
失敗時はdocs/RESUME.mdに従い公開完了済み工程snapshotから再開。ローカルだけを保存済みと呼ばない。現時点の監査はActions artifactとCIがReleaseから読戻したmanifestを用いており、各最終Release TAR本体をローカルへ再取得したという意味ではない。

## 入力と実行経路
再添付原寸PNG3枚はINPUTS.mdに記録された元画像とSHA256一致。GitHub/Release/blendに既存保存した300x400 WebPは実画素の派生画像であり代替生成画像ではない。これを各jobへ復元・持越し。原寸PNGのGitHubアップロードは未実施。今回は原寸を形状分析に使用し、テクスチャ貼付けはしない。
main開始HEAD a0038498903f950579e97dbddfde7b0f8d8c77efの実装/契約/ツール/schema/再開説明を確認。AGENTS.md該当なし。shell gitはDNS解決失敗、接続済みGitHub APIで非forceのmain更新、pushイベントActions起動、artifact実取得が成功。利用可能な検証済みruntimeを継続使用し、不要な再buildはしていない。
