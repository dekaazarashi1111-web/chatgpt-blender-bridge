# 進捗 / folded-rabbit-geometry-20260919

今回の対象は折れ耳・腕を下ろした添付オリジナルキャラクター。造形のみを仕上げる。テクスチャ、UV仕上げ、リグは別セッション。旧rabbit-geometry-20260918やstudio-smokeを今回の対象にしない。

## 現在の実行 — form-v003
source `c89554674a7ed6a55bcb6a2d0ecefb8ffcb7711f`。
Actions https://github.com/dekaazarashi1111-web/chatgpt-blender-bridge/actions/runs/35432676691 、attempt1。2026-09-19 08:41 UTC、pushイベントでin_progressを実確認。重複投入しない。
スクリプトと復元依存を先に揃え、job.jsonを最後に追加。実行予算18000秒、model/render/packageの3工程で保存。新しい造形の成功と視覚合格はまだ未確認。

v002の実画像レビューから、連続した鼻梁と二つの口元、より充実した眼球、滑らかな眼窩縁、傾斜した肩カバー、変化する断面の四肢、骨盤の稜線、指の関節と根元、丸い爪先、厚い折れ耳、蝶ネクタイ先端を修正。口元は偽の交差面を避けるため頭部と連続メッシュ化し、左右の編集用vertex groupを残す。未変更部品はfingerprint照合。受入済み親importを再実行しない。

## 最新の確認済み保存地点 — form-v002
source `72039ccb10a6b1b83d23f14abe84c46a6c416e45`。
Actions https://github.com/dekaazarashi1111-web/chatgpt-blender-bridge/actions/runs/35430997050 、attempt1、prepare/create成功、model/render/package全exit0、state=needs_review。
Release `creative-folded-rabbit-geometry-20260919-form-v002-35430997050-1-3`
- archive SHA256 `536ed187f54383979428459739169a9405394d76caf55476e5f74472306d5c4c`
- manifest SHA256 `2496607eb41d29ecc00d75a2f404c59f4c00d875df9ccb6cae0d368798663c47`
- resume blend `workspace/resume/output/model/model.blend`
- blend SHA256 `adbb099ed8f76fc69a6c309064ad82b04c472c6e8d8457a3b4be49b73374d3f3`

このセッションでhost/review ZIPを実取得し、API digest、Releaseから読み戻されたmanifest実バイトhash、全93出力のsize/hashを照合。両再読込検証成功、外部依存欠落なし。Release APIのassetも一致。最終Release archive本体をこの監査で再ダウンロードしたとは主張しない。v003のrunnerが指定archiveを復元・検証する。
実画像を開いて不一致を確認し、reviews/form-v002.mdへ保存。v002は完成扱いにしない。v001の検証と不合格理由はreviews/form-v001.md/jsonを参照。

## 次の確認
v003の同じActionsとworkspace-stateを追跡。終了後にログ、manifest、実出力、再読込、形状監査、13方向/詳細画像を確認し、原寸参照と比較する。問題は新job IDで修正し、対象版に固定したレビューと次の保存地点を記録する。
失敗ならdocs/RESUME.mdに従い、公開完了済みの有効な工程snapshotから再開する。ローカルだけのデータを保存済みと呼ばない。

## 入力
再添付された原寸PNG3枚のSHA256はINPUTS.mdの元画像と完全一致。比較用300x400 WebPの実画素とソースはGitHub/Release/blendに既存保存済みで、v003へ復元・持越し。原寸PNGそのもののGitHubアップロードは未実施。今回画像をテクスチャとして貼り付けない。
