# 進捗・引継ぎ

## 現在
新作品 `violet-rabbit-replica-20260918`。指示とバイト照合済み参照WebPはmain commit `7c95ee15b516f5846aa20871ffafb68e145a80c3` で保存済み。
`jobs/build-v001/` の制作・検証・梱包スクリプト5本を保存する段階。全ソースのローカル構文検査とGit blob SHA照合が完了。画像処理を実行し、実マップを開いて初期エラー（耳の境界を含む採取範囲）を投入前に修正した。詳細はdevelopment/build-v001-preflight.md。

まだjob.jsonは追加していない。Actionsは未投入。Release制作checkpointはまだない。ローカルのみのマップを遠隔保存済みと呼ばない。

## 次の作業
1. v2 job.jsonを最後に追加しmainのpush triggerを確認。source commitとrun URLを記録。
2. surfaces/model/lookdev/package、Release manifest readback、state、実画像を照合。
3. 対象版の造形・色・質感をレビューし、問題は新job IDで修正。現在の版は外観未確認。

## 再開
mainの本作品指示とworkspace-state/workspaces/violet-rabbit-replica-20260918/state.json、jobs、Actions、Release manifestを照合する。既存の別作品を今回の続きとして扱わない。
