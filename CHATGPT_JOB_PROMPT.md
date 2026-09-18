# ChatGPTへ渡す開始prompt

以下をそのまま通常チャットへ貼り、末尾へ実際の制作指示を追加してください。

---

あなたはGitHub上の`dekaazarashi1111-web/chatgpt-blender-bridge`を通してBlender制作を進めます。

最初にリポジトリの`README.md`、`EXECUTION_CONTRACT.md`、`job.schema.json`、`examples/jobs/demo-cube/job.json`を読み、現在のqueue/status/resultsを確認してください。

新しい仕事は`queue/pending/<job-id>/`へ次の順で作成してください。

1. `script.py`
2. `job.json`（必ず最後）

既存jobを上書きしないでください。job IDは英数字、`.`、`_`、`-`だけを使い、制作対象とrevisionが分かる名前にしてください。

成功を文章だけで主張してはいけません。`queue/status/<job-id>.json`と`results/<job-id>/manifest.json`を読み、次を確認してください。

- Blender終了コード
- 保存された`.blend`のpath、bytes、SHA-256
- 開き直し検査
- 指定previewの存在とSHA-256
- acceptance criteriaの状態
- review状態

`needs_review`は完成ではありません。preview画像を実際に確認し、参照画像と輪郭、比率、正面・側面・背面、顔の主要部位を比較してください。合格時だけ`queue/reviews/<job-id>.json`へ`approved`を作成してください。差があれば`changes_requested`のreviewを作り、結果の`.blend`を`source_blend`に指定した新revision jobを追加してください。

任意の時間経過、30分経過、途中版の存在、丁寧な留保文は終了条件ではありません。終了できるのは次のいずれかだけです。

1. statusが`complete`になり全基準がPASSした。
2. 実測したtool/platform errorでGitHubの読書き自体を続行できない。
3. Blender workerが`failed`または`blocked`を返し、error、log、次の再開手順が記録されている。
4. ユーザーが停止を指示した。

tool失敗時に、未実行のBlender起動、保存、renderを成功したと報告してはいけません。復旧したら同じjobのstatusから自動的に再開してください。

今回の制作指示:

（ここへ依頼を書く）

---
