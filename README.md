# ChatGPT Blender Bridge

GitHubをジョブキューとして使い、別のPCやサーバーでBlenderを継続実行するための公開ワークスペースです。

通常チャットはBlender用Pythonと`job.json`をGitHubへ追加します。常駐workerは`main`ブランチを監視し、信頼済みauthorのジョブだけをBlenderで実行します。結果の`.blend`、複数方向preview、検証report、ログ、SHA-256をGitHubへ返します。

```text
ChatGPT
  └─ queue/pending/<job-id>/script.py と job.json を作成
       ↓
GitHub main branch
       ↓ git pull
Blender worker
  ├─ author・schema・scriptを検証
  ├─ Blender background実行
  ├─ .blendを保存して開き直し検査
  ├─ 正面・側面・背面・斜めpreviewを生成
  └─ queue/status と resultsへ結果をpush
       ↓
ChatGPTがpreviewを比較し、reviewまたは次の修正jobを追加
```

このリポジトリは公開され、ジョブ、スクリプト、ログ、preview、公開可能な成果物はGitHub上から閲覧できます。

## 最短手順

1. [`START_HERE.md`](START_HERE.md)に従ってworkerを準備する。
2. `python bridge_cli.py doctor`でGit・GitHub・Blenderを確認する。
3. `python bridge_cli.py smoke`で実際のBlender保存・preview・再読込を確認する。
4. `python bridge_cli.py worker`を常駐させる。
5. [`CHATGPT_JOB_PROMPT.md`](CHATGPT_JOB_PROMPT.md)を通常チャットへ貼る。

WindowsとLinuxに対応します。Pythonの追加パッケージは不要です。Blender 4.x、Git、GitHub CLIを使います。

## 完成判定

workerが終了コード0を返しただけでは完成になりません。

- 出力`.blend`が存在する。
- Blenderで保存後のファイルを開き直せる。
- 指定した方向のpreviewがすべて存在する。
- 必須の自動基準がすべてPASSしている。
- `review_required=true`なら、preview確認後のreviewが`approved`である。

未達時は`failed`、`blocked`、`needs_review`、`changes_requested`のいずれかになり、`complete`にはなりません。詳しくは[`EXECUTION_CONTRACT.md`](EXECUTION_CONTRACT.md)を参照してください。

## ディレクトリ

| Path | 用途 |
|---|---|
| `queue/pending/` | ChatGPTが追加する実行job |
| `queue/reviews/` | preview確認後の判定 |
| `queue/status/` | workerが返す状態 |
| `results/` | report、preview、ログ、公開可能な`.blend` |
| `.worker/` | workerのlocal stateと全成果物。Git管理外 |
| `bridge/` | queue、検証、Blender実行コード |
| `examples/` | 動作確認job |

## 安全境界

- workerは`main`だけを監視します。
- `job.json`、`script.py`、入力`.blend`の最終commit authorが、すべて`config.json`の`trusted_authors`に一致する場合だけ実行します。
- ジョブscriptは許可moduleを静的検査し、`os`、`subprocess`、`socket`、`open`、`eval`等を拒否します。
- `source_blend`とscriptはリポジトリ内だけを参照できます。
- workerはBlender専用のOS userまたはcontainerで実行してください。
- pull requestのコードをworker上で実行しないでください。

## License

[MIT](LICENSE)
