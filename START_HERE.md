# 最初の準備と制作の始め方

新しい制作は GitHub Actions で実行します。Oracle、手元の Blender、常駐 worker は不要です。既存 worker の手順は [`docs/LEGACY_WORKER.md`](docs/LEGACY_WORKER.md) に移しました。

**このリポジトリでは実行環境の準備と制作・再開の実行確認を完了しています。通常は手順2から始めてください。** 検証した版と実行記録は [`docs/VERIFICATION.md`](docs/VERIFICATION.md) にあります。手順1はフォークした場合や実行環境を再構築する場合の説明です。

## 1. 初回・再構築時だけ制作環境を用意する

1. リポジトリの **Actions** を有効にする。
2. **Build creative runtime** の workflow（`runtime.yml`）を実行して完了を確認する。
3. GitHub Packages に `chatgpt-creative-runtime:runtime-v2` が作成されていることを確認する。
4. **Creative workspace** の workflow（`creative-job.yml`）で同梱の v2 サンプルを実行し、ログ・出力・保存先を確認する。

サンプルは [Blender の保存・4方向プレビュー](projects/studio-smoke/jobs/blender-v001/job.json) と [画像生成・リサイズ・Krita 書き出し](projects/studio-smoke/jobs/texture-v001/job.json) です。これらの `review_required=false` は技術動作確認用です。参考画像に合わせて作る実作品では、品質レビューを有効にしてください。

ワークフロー名の表示が異なる場合は括弧内のファイル名で探してください。runtime は Blender・画像処理ツールを入れた共通環境です。毎回ソフトをインストールせず、この環境を取得して制作を始めます。環境を変更したときは `runtime.yml` を再実行します。

Actions は `GITHUB_TOKEN` を使って実行環境と成果物を管理します。通常の同一リポジトリ運用に個人の PAT を設定する必要はありません。

実行環境の参照先は `ghcr.io/<owner>/chatgpt-creative-runtime:runtime-v2` です。制作開始時にイメージの digest を解決して記録し、どの環境で実行したか追跡します。ソフトのバージョンは runtime の実際の出力を確認してください。過去の会話で挙がった Blender のバージョンがそのまま導入されているとは限りません。

## 2. 同じプロンプトと画像を渡す

[`CHATGPT_JOB_PROMPT.md`](CHATGPT_JOB_PROMPT.md) の短いプロンプトと、参考画像・制作依頼を ChatGPT へ渡してください。GitHub へ読み書きできる接続が必要です。

ChatGPT は作品の brief、決定事項、入力、ジョブを `projects/<project_id>/` に保存します。ジョブ本体は次の場所です。

```text
projects/<project_id>/jobs/<job_id>/job.json
```

ファイル名や項目を会話から推測せず、現在の schema とサンプルを読みます。制作処理は `tools.json` に登録されたツールから選びます。

**添付画像は自動的には Actions へ届きません。** 画像を実際に加工したり、テクスチャとして使ったりする場合は、実ファイルを入力として保存する必要があります。[`docs/INPUTS.md`](docs/INPUTS.md) を確認してください。

## 3. ジョブを起動する

新しい v2 ジョブを既定ブランチへ追加したときは、workflow の push 条件に従って対象を検出します。手動では Actions の `creative-job.yml` の **Run workflow** を使い、`job_path` に対象の `job.json` を指定します。空欄は未実行の対象ジョブを検出します。

GitHub CLI を使える環境からの例です。

```bash
gh workflow run creative-job.yml \
  --repo dekaazarashi1111-web/chatgpt-blender-bridge \
  -f job_path=projects/my-project/jobs/model-v001/job.json
```

`my-project` と `model-v001` は実在する作品とジョブへ置き換えます。GitHub 接続では、ファイルの追加・更新とブランチ更新による push 起動も使えます。いずれも Actions の実行 URL を確認してから「投入済み」と扱ってください。

1 回の検出は最大 32 件で、現在は順番に実行します。同時に重複実行しないよう workflow 全体を制御します。大量の未実行ジョブを置くより、前の工程の結果を確認してから次のジョブを作る方が制作に適しています。

## 4. 結果を見る

| 場所 | 確認するもの |
|---|---|
| Actions の実行 | step の成功・失敗、ツールのログ |
| `workspace-state` ブランチの `workspaces/<project_id>/state.json` | 作品の現在の状態と最新保存地点 |
| 同ブランチの `workspaces/<project_id>/jobs/<job_id>.json` | 対象ジョブの状態・実行情報・snapshot |
| 状態から参照される Release | 制作ファイル、manifest、復元するアーカイブ |
| Actions artifact | 調査用のログや出力。保存期限がある |

ツールが正常終了しただけでは完成ではありません。Blender なら保存後の開き直し検査とプレビューを、テクスチャなら画像そのものと必要なマップを確認します。レビューが必要なジョブは対象版のレビューを追加します。詳細は [`EXECUTION_CONTRACT.md`](EXECUTION_CONTRACT.md) と [`docs/REVIEW.md`](docs/REVIEW.md) にあります。

## 5. 別セッションで再開する

同じ短い開始プロンプトへ作品 ID と「続きから」を付けて渡してください。新しい ChatGPT は `workspace-state` を読み、まだ動いているジョブを確認します。

- 実行中なら新規ジョブを重ねず、既存の実行を確認する。
- 停止・失敗していたら、最後に保存できた snapshot を復元する。
- 完了済みなら、成果物とレビューを読み、次の作業へ進む。

復元できるのは保存済みのファイルです。途中のメモリ状態は引き継がれません。[`docs/RESUME.md`](docs/RESUME.md) に具体的な再開情報をまとめています。
