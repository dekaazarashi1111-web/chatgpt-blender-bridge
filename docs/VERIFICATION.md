# 実行確認記録

2026年9月18日に、このリポジトリの GitHub Actions で実行環境の構築、制作、成果物の保存、保存済み `.blend` からの再開を確認しました。

## 実行と確認結果

| 対象 | 実行記録 | 結果 |
|---|---|---|
| runtime 構築・実ツール検証 | [run 35353265216](https://github.com/dekaazarashi1111-web/chatgpt-blender-bridge/actions/runs/35353265216) | ネットワークなしで画像生成、リサイズ、Krita の ORA 書き出し、動画化、サムネイル、Blender の6操作に成功 |
| Blender・テクスチャ制作 | [run 35353573199](https://github.com/dekaazarashi1111-web/chatgpt-blender-bridge/actions/runs/35353573199) | `blender-v001` と `texture-v001` が `complete`。Release 保存と状態更新に成功 |
| 保存データからの再開 | [run 35353761801](https://github.com/dekaazarashi1111-web/chatgpt-blender-bridge/actions/runs/35353761801) | `blender-resume-v001` が `complete`。復元したモデルのメッシュ・単位・材質を確認してから変更し、保存後に再読込 |
| schema・単体テスト | [run 35354225390](https://github.com/dekaazarashi1111-web/chatgpt-blender-bridge/actions/runs/35354225390) | `jsonschema` を導入した CI で54件成功、skip なし。既存・新規ジョブの定義検査も成功 |

Blender は画像を pack した編集可能なファイル、4方向プレビュー、保存後の再読込を検証しました。制作と再開の状態記録では `publication_errors` は空でした。初回 Blender 成果物は別のローカル環境でも SHA-256 を照合して復元し、青いキューブのプレビューを実際に確認しました。再開後の銅色のモデルも、GitHub に保存された斜めプレビューを開いて確認しました。

ローカルの単体テストは54件実行、1件 skip でした。skip はローカルに `jsonschema` がないためです。

## 保存済み成果物

| ジョブ | 状態 | Release |
|---|---|---|
| `blender-v001` | [状態 JSON](https://github.com/dekaazarashi1111-web/chatgpt-blender-bridge/blob/workspace-state/workspaces/studio-smoke/jobs/blender-v001.json) | [初回 Blender](https://github.com/dekaazarashi1111-web/chatgpt-blender-bridge/releases/tag/creative-studio-smoke-blender-v001-35353573199-1-1) |
| `texture-v001` | [状態 JSON](https://github.com/dekaazarashi1111-web/chatgpt-blender-bridge/blob/workspace-state/workspaces/studio-smoke/jobs/texture-v001.json) | [テクスチャ最終工程](https://github.com/dekaazarashi1111-web/chatgpt-blender-bridge/releases/tag/creative-studio-smoke-texture-v001-35353573199-1-3) |
| `blender-resume-v001` | [状態 JSON](https://github.com/dekaazarashi1111-web/chatgpt-blender-bridge/blob/workspace-state/workspaces/studio-smoke/jobs/blender-resume-v001.json) | [再開後の Blender](https://github.com/dekaazarashi1111-web/chatgpt-blender-bridge/releases/tag/creative-studio-smoke-blender-resume-v001-35353761801-1-2) |

## 検証した版

| 対象 | commit |
|---|---|
| runtime | `27e8dc79512ddaca279d90f19fb701aff550e72a` |
| 制作ジョブ | `925ad076d5721956bfc0f48349ac918e2acb1807` |
| 再開 | `5007df31ab31903cae4a2526bf3dac1a861e9930` |
| schema・単体テスト CI | `9257fd0bf0466a32818c53bf2683f96aa938afcd` |

検証済みイメージは次の digest です。

```text
ghcr.io/dekaazarashi1111-web/chatgpt-creative-runtime@sha256:3e7adf0a7a1aaab0f218c3a6c8ac572a14b266d21cbafcd74acc19573d62e5b6
```

| ソフト | 実測バージョン |
|---|---|
| Blender | 4.0.2 |
| Krita | 5.2.2 |
| FFmpeg | 6.1.1 |
| ImageMagick | 6.9.12 |
| Python | 3.12.3 |
| Pillow | 10.2 |
| NumPy | 1.26.4 |

制作予算の既定5時間・最大5時間半は設定値です。5時間連続の負荷試験を完了したという意味ではありません。この確認は技術動作のサンプルを対象とし、実作品の品質レビューは各制作で行います。参考画像の実ファイルは別途 GitHub へ保存する必要があり、チャット添付の自動転送は含みません。Material Maker は未導入です。
