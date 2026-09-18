# 進捗・引継ぎ

## 現在
作品ID `violet-rabbit-replica-20260918`。新規制作。
- 指示・実バイト照合済み参照WebPを保存: `7c95ee15b516f5846aa20871ffafb68e145a80c3`。
- 制作ソース5本、検証・記録を保存: `051af2bdd743b34c65598ecd8ee13f8c6a5705e2`。
- v2 job定義を最後に追加したsource commit: `fa62aa2422961ed324297bf23440c3cbb493282f`。
- job ID: `build-v001`。
- 実際にpush triggerで起動したActions: https://github.com/dekaazarashi1111-web/chatgpt-blender-bridge/actions/runs/35372299694
- 2026-09-18T17:05:39Zに起動。prepareの実行とレビュー適用成功を確認。重複投入しない。

ソースはローカル構文検査とGit blob SHA照合を通過。参照画像からの材質マップをローカルで実際に作成して開き、耳の不適切な採取範囲を投入前に修正。詳細はdevelopment/build-v001-preflight.md。GitHub側のBlender実行・保存・実画像レビューはまだ進行待ち。現在の版の外観を確認済みとはしない。

## 実行工程
surfaces -> model -> lookdev -> package。
形状・材質生成後、packed .blendの保存後再読込、7枚の768px Cycles画像、三面比較、全依存とソースを含む納品パッケージを作る。制作合計予算18000秒、個別上限はjob定義を参照。

## 次の作業
1. 上記Actionsとworkspace-stateの本作品state/jobsを追跡。実行中なら新jobを投げない。
2. 実行ログ、Releaseのmanifest readback・size/SHA-256、再読込と画像の自動検査を照合。
3. comparison、face、face_profile、surface、正面／側面／背面を実際に開く。造形と質感を参考画像と比較して本版レビューを保存。
4. 不一致は受入済みの無関係工程をやり直さず、有効な保存済みsnapshotから新job IDで修正。

## 保存地点
まだこの記録ではReleaseの読戻しを確認していない。実データのリモート保存は状態とmanifestを照合した後にここへ記録する。

## 再開
mainの本作品brief/decisions/reviewsとworkspace-state/workspaces/violet-rabbit-replica-20260918/state.json、jobs/build-v001.json、Actions、Release manifestを照合。復元には記録のrelease_tag/project_id/job_id/archive_sha256/manifest_sha256をそのまま使う。既存の別作品 `worn-violet-rabbit-20260918` は今回の続きではない。
