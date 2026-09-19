# 進捗 / 再開ポイント

## 現在: form-v003 実行中、重複投入禁止
2026-09-19 の依頼も造形のみ。テクスチャ、UV仕上げ、リグは開始しない。
開始時main `18a05d7d2de20618c9002db243340fd685f37089` の開始プロンプト・規約・schema・ツール・説明・作品指示と実装を確認。再帰tree内にAGENTS.mdは検出されなかった。shell DNSは失敗するがGitHub接続の読み書きとartifact downloadは利用できた。

古い『v002未投入』メモは誤りで、v002はすでに完了していた。実画像を読み、顎・眼窩・曲面の段差・手指・爪先等の修正要求をreviews/form-v002.md/.jsonに保存した。v002を重複実行していない。

スクリプト先行commit `ee60639f9900120ed51c8d4c043d951786e827ff`。
新規job.json投入source `0aa4a5c068c925266e536b582a329bd273ceccf1`。
実際のActions https://github.com/dekaazarashi1111-web/chatgpt-blender-bridge/actions/runs/35427795287 （attempt 1）。
workspace-state jobs/form-v003.jsonはrunning、開始06:54:11Z。このメモ時点でv003の新規Release保存・実画像レビューは未確認。まずこの実行を追跡する。

## 有効な直前の制作保存地点
job `form-v002` / source `0fdebb95a32118f8bfa2e75da4ee0ecb2de23170`
Actions https://github.com/dekaazarashi1111-web/chatgpt-blender-bridge/actions/runs/35390326287
Release tag `creative-rabbit-geometry-20260918-form-v002-35390326287-1-3`
archive SHA256 `93dbd6936c126531da994e2ac3905af380b84f362275e5064f33d4ebf6cdb123`
manifest SHA256 `d61ae5dce72b2b3480183cc76a8387ede3804026d3ec91ec18c2a1bb5c89f1b1`
再開source_blend `workspace/resume/output/model/model.blend`
モデルSHA256 `f028acd02a8dd1ddd57f64d260e75fb50382151c72668cb1ea0fec39bc8f1f4f`

## 次の作業
v003完了後、その版のRelease/state/manifest/ログを照合し、実際の全身3方向、顔、単色クレイ、耳、手、足の画像を参考画像と比較する。実行成功だけで完成扱いしない。残る差異があれば新しいjob IDで修正し、レビューと保存地点を更新する。v003は頭部・耳・手足・蝶ネクタイを編集、胴・脚・内部ジョイント等の未変更部位はfingerprint照合で保持している。

## 失敗した方法と履歴
reviews/form-v001.mdとform-v002.mdに実画像の不合格理由、過大なmouth cutter、C1断面補間の帯状陰影、指の端面、比較マスク手法の限界を保存。局所checkpointはリモート公開されるまで保存済みと呼ばない。工程内で中断した場合はmanifestの実パスを確認し、docs/RESUME.mdに従う。
