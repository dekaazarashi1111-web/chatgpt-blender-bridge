# 実行契約

## 状態

| Status | 意味 |
|---|---|
| `pending` | 未着手 |
| `running` | workerがclaimしBlenderを実行中 |
| `needs_review` | 技術検証PASS。画像による品質確認待ち |
| `changes_requested` | preview確認で修正が必要 |
| `complete` | 技術検証と必要なreviewがすべてPASS |
| `failed` | 実行または検証に失敗 |
| `blocked` | 入力不足など、外部対応が必要 |

## 完了gate

`complete`には次をすべて要求します。

1. ジョブschemaが有効である。
2. authorが`trusted_authors`に含まれる。
3. Blender processの終了コードが0である。
4. `.blend`が保存され、空でない。
5. 保存ファイルをBlenderで開き直し、検査reportを生成できる。
6. 指定previewがすべて存在し、空でない。
7. 必須automatic criterionがすべてPASSである。
8. `review_required=true`の場合、reviewが`approved`である。

## 中断と再開

- `running`へ移る前にstatusをGitHubへ記録します。
- Blender内の`checkpoint()`は`.worker/runs/<job-id>/checkpoint.json`をatomic更新します。
- timeoutやprocess異常終了でもlog、checkpoint、途中成果をlocal run directoryへ残します。
- 同じjob IDは自動再実行しません。原因修正後は新しいrevision jobを追加します。
- `complete`以外を完成品として報告しません。

## 信頼境界

- workerは`main`ブランチだけをpollします。
- GitHub APIが返すcommit author loginを検査します。
- 許可外moduleや危険builtinを含むPythonはBlender起動前に拒否します。
- path traversal、絶対path、リポジトリ外sourceは拒否します。
- workerのOS userがアクセスできる範囲を最小化します。
- Blender scriptは強いsandboxではありません。workerは制作専用環境で動かします。
