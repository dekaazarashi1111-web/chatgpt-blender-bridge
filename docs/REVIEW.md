# 成果物のレビュー

ChatGPT が行う品質レビューは「処理が動いた」と「依頼に合っている」を分けるために行います。制作ファイルとプレビューの自動検査が通ってから、対象版の画像を実際に確認してください。

## 保存先と形式

```text
projects/<project_id>/reviews/<job_id>.json
```

レビューの内容は次の形式です。hash と commit は対象ジョブの状態から取得します。

```json
{
  "schema_version": 1,
  "project_id": "my-project",
  "job_id": "model-v001",
  "source_commit": "対象ジョブの実行元 commit",
  "snapshot_sha256": "latest_snapshot.archive_sha256 の値",
  "verdict": "approved",
  "criteria": {
    "ジョブの acceptance_criteria に記載した基準": "pass"
  },
  "summary": "実際に確認した画像、比較結果、残課題を記載"
}
```

例示値をそのまま使わないでください。`criteria` はジョブのすべての acceptance_criteria の基準に対応させ、それぞれ `pass` または `fail` を記録します。修正が必要な場合は `verdict` を `changes_requested` にします。

source commit と snapshot の SHA-256 が対象版に一致しなければ、その版の品質判定として使用できません。各版の画像と検査結果を確認してください。

## 見るもの

- **モデル**：輪郭、全体と各部の比率、必要な方向からの見た目、パーツの欠落。
- **テクスチャ**：参考との色・柄・粗さの違い、必要なマップの有無、継ぎ目や解像度。
- **制作データ**：編集可能な元データ、依存する画像や素材、manifest と検査結果。

参考画像のない背面などは推定であることを brief に残します。プレビューの画角や照明で分からない箇所を確認済みにしないでください。

レビューを追加した push は状態の再評価の対象になります。品質判定の結果は `workspace-state` の該当ジョブで確認してください。レビュー JSON を置いただけで、必須検査が失敗したジョブが成功へ変わるわけではありません。
