# 別セッションからの再開

## どこに何を残すか

| 保存先 | 内容 |
|---|---|
| 通常のソースブランチ `projects/<project_id>/` | brief、決定事項、入力、スクリプト、ジョブ、レビュー |
| `workspace-state` ブランチ `workspaces/<project_id>/state.json` | 作品の進捗と最新保存先 |
| 同ブランチ `workspaces/<project_id>/jobs/<job_id>.json` | 各実行の状態と保存情報 |
| 状態が指す Release | 実際の制作ファイルの snapshot と manifest |
| Actions artifact | 一時的な確認・調査用ファイル |

`workspace-state` は成果物から自動更新するためのブランチです。普段のソース編集と分けて、複数ジョブによるコミットの競合を減らします。Actions の作業ディスクやキャッシュは永続ワークスペースではありません。

## 再開の手順

1. 作品の brief・決定事項・レビューを読む。
2. 対象ジョブの状態と実際の Actions の状態を照合する。チャットが切れただけなら Actions は通常続いている。
3. 使用する保存地点を選び、その snapshot の識別情報を取得する。最新保存先は `latest_snapshot`、完了済み step ごとの全作業領域の保存先は `step_snapshots[step_id]` にある。
4. 新しい job ID の v2 ジョブに `resume` を指定する。
5. SHA-256 検証を通った復元データを入力にして、必要な工程を実行する。

`resume` に必要な情報は以下です。値を捏造せず、保存済み記録からコピーしてください。

```json
{
  "release_tag": "状態に記録された Release の tag",
  "project_id": "保存元の作品 ID",
  "job_id": "保存元のジョブ ID",
  "archive_sha256": "状態に記録されたアーカイブの SHA-256",
  "manifest_sha256": "状態に記録された manifest の SHA-256"
}
```

これは項目の説明用です。日本語の例示値を実際のジョブへ使わないでください。ジョブ全体の書式は v2 schema とサンプルを参照してください。

## 復元したファイルを使う

保存データは制作コンテナ内の `/work/resume` へ展開されます。ジョブのパスでは `workspace/resume/` 以下を参照します。

| snapshot の種類 | Blender の `source_blend` の例 |
|---|---|
| スクリプトが保存した checkpoint | `workspace/resume/scene.blend` |
| 工程・ジョブの出力を含む snapshot | `workspace/resume/output/<step_id>/model.blend` |

実際の相対パスは manifest を確認してください。すべての snapshot に `scene.blend` があるわけではありません。画像・テクスチャも同様に manifest 内のパスを使います。

定期 checkpoint は現在の step の出力を保存するため、それ以前の全 step のデータを含むとは限りません。複数の工程出力が必要なら `step_snapshots[step_id]` の全作業領域の snapshot を選びます。全作業領域の snapshot では、履歴が再帰的に増えないよう `checkpoints/` と `resume/` を除外しています。復元したデータを次の保存先でも使う場合は、必要な依存ファイルを現在の `output/` へコピーするか、Blender ファイルへ pack してください。

Blender の保存処理は画像とリンクされたライブラリを pack します。ただし、すべての外部メディアやシミュレーションキャッシュが自動的に収録される保証はありません。必要な依存ファイルが snapshot に含まれることを確認してください。

## 途中保存の考え方

checkpoint は「ここまで終わった」という文章だけではありません。再開に必要な `.blend`、テクスチャ、材質の元データを保存し、それらを snapshot として公開して初めて再開地点になります。

runner は現在の step に属する、確定済みの最新 checkpoint を選んで保存します。定期公開の間隔は `max(120秒, timeout_seconds / 10)`、最大 12 回です。既定の 5 時間予算では約 30 分ごと、最大の 5 時間半では約 33 分ごとが目安で、公開できる checkpoint が存在するときだけ処理します。工程完了時の保存はこの 12 回とは別に行い、失敗時も保存を試みます。

ローカルで `checkpoint()` を呼ぶ間隔と、GitHub へ公開する間隔は異なります。細かい節目の checkpoint を作っても、直ちにリモート保存されたとは扱いません。造形・UV・材質を個別の step に分ければ、工程が完了するたびに全作業領域を保存できます。

制作ファイルの保存が完了する前に checkpoint を公開対象にしないでください。書き込み途中のファイルをコピーすると、アーカイブができても Blender で開けない可能性があります。Python / Blender の script には `checkpoint(stage, summary="", evidence=None)` が提供されます。例えば Blender の造形後に `checkpoint("geometry", "基本形状を保存")` を呼びます。Blender は画像を pack して `.blend` を保存し、Python は `OUTPUT_DIR` 内の完成済みファイルをコピーします。

checkpoint の確定先は `checkpoints/<step_id>/<UTC日時>-<stage>/` です。runner はコピー完了後の `checkpoint.json` があるディレクトリだけを公開対象にします。完成済み checkpoint は上書きせず、新しい出力は `OUTPUT_DIR` へ書いてください。詳細な API は [`../runtime/README.md`](../runtime/README.md) にあります。

## 保存が途切れた場合

- **ChatGPT だけが切断**：Actions の状態を確認する。保存済み状態から新しいチャットが状況を理解できる。
- **Blender が失敗**：ログと最後の有効な snapshot を読み、新しいジョブで修正する。
- **Actions が強制終了**：最後に GitHub への公開が完了した地点まで復元できる。
- **Release は保存済みだが状態更新に失敗**：実行ログと Release を確認し、manifest と hash が一致する保存先を特定する。
- **hash が一致しない**：復元を止める。違う snapshot の情報を混ぜていないか確認する。

Release の asset を削除・置換すると再開できなくなります。参照中の snapshot は上書きせず保持してください。GitHub の保存先に残せることは、無制限の容量や永久保存の保証ではありません。
