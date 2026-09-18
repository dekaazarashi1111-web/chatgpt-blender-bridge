# 参考画像と素材の入力

## チャットの画像と制作入力は別

ChatGPT が添付画像を見られる場合でも、Actions のコンテナはその添付ファイルを自動的に読めません。

- **画像を見て形状や配色を考える**：ChatGPT が画像を読み、制作指示とスクリプトへ反映できる。
- **画像を加工する・テクスチャとして貼る**：画像の実バイトを保存し、Actions の入力にする必要がある。

後者では元画像の保存ができていないのに、代替画像を作って「参考画像を取り込んだ」と扱わないでください。

## 保存の方針

作品の入力は `projects/<project_id>/inputs/` にまとめ、元ファイル名、役割、入手元を brief か入力一覧へ記録します。ジョブの `inputs` には `path`（`projects/<project_id>/inputs/` または `source/` 以下）、`target`（コンテナへ配置する相対パス）、`sha256`（元ファイルの SHA-256）を指定します。例えば target が `references/front.png` なら、ツールの入力は `input/references/front.png`、script では `INPUT_DIR / "references/front.png"` です。SHA-256 が一致しない入力は受け付けません。

GitHub 接続でバイナリを直接アップロードできるなら、その操作で保存します。ローカル実行環境を使える場合は、同梱 helper でファイルを配置し、job 用の入力定義を生成できます。

入力が大きい場合は Release などの保存先から runner 側で事前取得する経路が必要です。取得したファイルをジョブの入力として記録し、再開時にも同じデータを使えるよう保存します。

## 入力を配置する helper

リポジトリのルートで実行します。`--source` は取得済みの実ファイル、`--target` は作品の `inputs/` 以下に配置する相対パスです。

```bash
python ci/import_reference.py \
  --project my-project \
  --source /path/to/front.png \
  --target references/front.png
```

元画像の実バイトを base64 にしたテキストファイルがある場合は、`--base64` を付けます。

```bash
python ci/import_reference.py \
  --project my-project \
  --source /path/to/front.png.base64 \
  --target references/front.png \
  --base64
```

helper はローカルの `projects/my-project/inputs/references/front.png` を新規作成し、`path`・`target`・`sha256` の JSON を出力します。その JSON を job の `inputs` 配列へ追加します。既存ファイルは上書きせず、デコード後のサイズは最大 20 MiB です。

helper で作成したファイルは、Git の commit/push または GitHub 接続の blob・tree・commit・ref 操作で保存し、続けてジョブを追加します。添付画像の実バイト取得、入力の配置、GitHub への保存をそれぞれ確認します。シェルのネットワークと GitHub 接続は別の経路として扱い、利用できる経路で保存します。

## 再現性

- 入力と script が揃った後にジョブ定義を追加し、実行対象 commit を固定する。
- 入力を変えて再制作する場合は新しい job ID を使う。
- 外部依存テクスチャは出力 snapshot に含めるか、Blender ファイルへ pack する。
- 復元対象の入力・成果物は manifest のサイズと SHA-256 で照合する。

追加素材は取得元とファイルを記録します。手元の入力や制作ツールで生成した素材も利用できます。
