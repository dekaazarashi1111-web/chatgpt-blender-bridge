# 進捗・引継ぎ

作品ID `violet-rabbit-replica-20260918`。新規制作。別作品worn-violet-rabbit-20260918とは別。

## 完了
指示・全体参考WebP: main7c95ee15。初版ソース:051af2bd。初版job/source: `fa62aa2422961ed324297bf23440c3cbb493282f`。
`build-v001` 実行: https://github.com/dekaazarashi1111-web/chatgpt-blender-bridge/actions/runs/35372299694
4工程成功、packed .blend、編集可能マップ、ソース、実比較画像をRelease保存。再読込欠落0、実際にダウンロードした83ファイルを読戻しmanifestとサイズ/SHA照合した。詳しくはreviews/build-v001.md。

## 外観レビュー
**changes_requested**。初版は最終完成ではない。実画像で明るさ、模様のぼけ、側面顎、鼻の接続、耳の形、腹当て／蝶ネクタイのめり込み、欠損境界、足先に問題を認めた。レビューJSONは実source/snapshotへpinした。

## 現在の修正
`jobs/refine-v002/` の4スクリプトと元PNGの無劣化採取3入力をmainへ保存する段階。ローカル構文・転送SHA検査済み。新マップを実生成して開いた。Blenderでの修正結果はまだ未実行・未確認。job.jsonはまだ追加していない。

## 有効な保存地点
release_tag `creative-violet-rabbit-replica-20260918-build-v001-35372299694-1-4`
project_id `violet-rabbit-replica-20260918`, job_id `build-v001`
archive_sha256 `3983aa75878c17d00535d3c9dda4d9992a2a5f4ee5dc28cc5548225ef0a6502b`
manifest_sha256 `cecd13eb98bb4a9fc8e435de844673af67d9d05607a7bb9964c5de4f80fe33d2`
resume blend `workspace/resume/output/lookdev/model.blend`。

## 次の作業
新v2 job refine-v002を入力とスクリプト保存後に最後に追加し、上記snapshotから復元する。surfaces→model→lookdev→package。Actionsとstateを追跡し、実行中は重複投入しない。失敗時は最新有効snapshotとlogsを照合して新IDへ。成功後も実比較・顔・側面・表面を開き、必要なら部分修正を続ける。結果のsource/run/snapshot/レビューをここへ更新。
