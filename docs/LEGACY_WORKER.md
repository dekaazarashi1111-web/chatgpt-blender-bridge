# v1 常駐 worker（互換用）

この手順は既存の v1 worker 用です。新規制作は [Actions の手順](../START_HERE.md) を使えます。Oracle や常駐 worker は標準構成では不要です。

## 1. 必要なもの

- Python 3.11以上
- Git
- GitHub CLI (`gh`)
- Blender 4.x
- このリポジトリへcommitできるGitHubアカウント

## 2. cloneと設定

```bash
git clone https://github.com/dekaazarashi1111-web/chatgpt-blender-bridge.git
cd chatgpt-blender-bridge
cp config.example.json config.json
```

Windows PowerShellでは次を使えます。

```powershell
./scripts/setup_windows.ps1
```

Linuxでは次を使えます。

```bash
bash scripts/setup_linux.sh
```

`config.json`の`blender_bin`が空なら、PATHと一般的なinstall先から自動検出します。検出されない場合だけ絶対pathを指定してください。

## 3. 認証と診断

```bash
gh auth login
gh auth setup-git
python bridge_cli.py doctor
```

`DOCTOR=PASS`になるまでworkerを常駐させないでください。

## 4. Blender smoke test

```bash
python bridge_cli.py smoke
```

合格時は`.worker/smoke/latest/`に次が作られます。

- `output/model.blend`
- `previews/front.png`
- `previews/right.png`
- `previews/back.png`
- `previews/three_quarter.png`
- `validation.json`
- `manifest.json`

## 5. worker起動

一度だけ処理:

```bash
python bridge_cli.py worker --once
```

常駐:

```bash
python bridge_cli.py worker
```

Windowsならタスクスケジューラ、Linuxならsystemd等で`python bridge_cli.py worker`を再起動可能にしておくと安定します。

## 6. ChatGPTからjobを追加

v1 を明示して使う場合は `job.schema.json` と `examples/jobs/demo-cube/` に従い、参照画像と制作指示からジョブを作成します。現在の開始プロンプトは v2 を既定にしているため、v1 worker 用のジョブ形式と混同しないでください。

ChatGPTは次の順でファイルを作ります。

1. `queue/pending/<job-id>/script.py`
2. `queue/pending/<job-id>/job.json`（最後に作成）

`job.json`が追加された時点でworkerが処理対象として認識します。

## 7. 結果確認と修正

結果は次へ返ります。

```text
queue/status/<job-id>.json
results/<job-id>/manifest.json
results/<job-id>/previews/*.png
results/<job-id>/blender.log
```

`needs_review`ならpreviewを確認します。合格なら`queue/reviews/<job-id>.json`を追加し、不一致があれば元の結果を`source_blend`に指定した新しいjobを追加します。

同じjobを上書きせず、`character-v002`、`character-v003`のように新しいIDで履歴を残してください。
