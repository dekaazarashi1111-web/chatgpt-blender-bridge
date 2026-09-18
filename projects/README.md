# 作品ごとのワークスペース

1 作品につき固定の `project_id` を使います。修正は同じ作品内に新しい `job_id` を作り、過去の入力・script・結果との対応を残します。

| パス | 内容 |
|---|---|
| `<project_id>/brief.md` | 制作目的、参考画像の意味、寸法、納品形式、品質基準 |
| `<project_id>/decisions.md` | 決定事項、変更理由、失敗した方法、次の課題 |
| `<project_id>/inputs/` | 参考画像や制作に必要な入力 |
| `<project_id>/jobs/<job_id>/job.json` | schema version 2 のジョブ定義 |
| `<project_id>/jobs/<job_id>/` の補助ファイル | script、設定など |
| `<project_id>/reviews/<job_id>.json` | 対象の成果物に紐付いたレビュー |

実行状態はこのブランチへ書き戻すのではなく、`workspace-state` ブランチの `workspaces/<project_id>/` に記録します。大きな制作ファイルは状態が参照する Release にあります。

## brief に残す項目

- 何を、何の用途に作るか。
- 参考画像のファイルと役割。正面・側面・素材見本など。
- 必要なサイズ、色、納品形式と編集可能な元データ。
- 自動検査で確認する項目と、画像で判断する完成基準。
- 未指定のために採用した既定値、推定した箇所。

特定のキャラクターや部屋だけに固定しません。小物、キャラクター、背景、テクスチャを同じ入口で扱い、ツールと工程は依頼に合わせて選びます。

## 別セッションへの引き継ぎ

作品 ID を伝えれば、新しい ChatGPT は brief、decisions、レビュー、`workspace-state`、保存済み manifest を順に読めます。現在のチャット内だけに「次は何をするか」を残さないでください。

詳細は [`../CHATGPT_JOB_PROMPT.md`](../CHATGPT_JOB_PROMPT.md) と [`../docs/RESUME.md`](../docs/RESUME.md) を参照してください。
