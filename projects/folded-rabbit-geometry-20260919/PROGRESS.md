# 進捗 / folded-rabbit-geometry-20260919

対象は2026-09-19に添付された折れ耳・腕下ろしの3面図。今回の範囲は造形のみ。旧rabbit-geometry-20260918のTポーズ版や並行form-v004は別の制作対象として残している。

## 現在の実行 — form-v002
source `72039ccb10a6b1b83d23f14abe84c46a6c416e45`。
Actions https://github.com/dekaazarashi1111-web/chatgpt-blender-bridge/actions/runs/35430997050 、attempt1、2026-09-19 08:04 UTCに実際のpush起動を確認。実行中は重複投入しない。v002の生成成功・視覚受入はまだ未確認。

## 直前の保存とレビュー — form-v001
source `0eb25f886539d7aa9b4b37b60337a46c75ebd086`。
Actions https://github.com/dekaazarashi1111-web/chatgpt-blender-bridge/actions/runs/35429889918 、attempt1、全4工程exit0。
最終Release `creative-folded-rabbit-geometry-20260919-form-v001-35429889918-1-4`
- archive SHA256 `d22896786f350e02e96e07920797a619dbfc076d85f855bcb1352329da33ec77`
- manifest SHA256 `eda577fc0f024e9259fff0eae2f747db2c0a8b4c243903e0769c1f9595316807`
- 再開元blend `workspace/resume/output/model/model.blend`
- blend SHA256 `76f7e0926c7ebdcc45b34e0f608ebe5b7de9c77d77999b859b0948b85dd6e3ef`

host/review ZIPを実取得。API digest、Release manifest実バイトhash、全80出力のsize/hash、両Blender再読込、必須部品と主要閉曲面を検査済み。原寸の新しいPNGと実際の全身/頭部/耳/手/足画像を比較し、不一致を認めた。レビューはreviews/form-v001.mdと同jsonに正確なsource/archiveを固定して保存。実行成功だけで完成とはしていない。

## v002の修正
眼球を顔面内へ沈め、浮くリングを撤去。鼻梁とマズルを連続化、頬を球でなく参照形のパッドに、歯を口腔内へ配置。耳先の余計な板を撤去し、前方への折れを深めて高さを調整。腕・手掌の箱状面を曲面化し、指根元、膝/骨盤、太い爪先、ネクタイの厚みを修正。
受入済み親importは再実行せず、同一projectのv001最終snapshotから継承。未変更部品のfingerprintを検査。3工程の新ジョブで実行し、既存の検証済みレンダー/パッケージ実装をhash確認して利用する。

## 次の確認
同じv002 Actionsとworkspace-stateを追跡。完了後、実画像/ログ/manifestを取得して検証・比較し、必要なら新job IDで修正する。対象版のレビューと保存地点を更新する。失敗時はdocs/RESUME.mdに従い有効な工程snapshotへ戻る。現在のローカルデータだけを保存済みとは扱わない。

入力は実画素から作成した3枚の縮小WebPをGitHubとblendへ保存済み。原寸PNGのGitHub保存は未実施（INPUTS参照）。次回のテクスチャ制作は今回の造形完成版の承認状態を確認してから行う。
