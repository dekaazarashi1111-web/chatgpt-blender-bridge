# 制作ツールの選び方と追加

## 登録されている操作を選ぶ

`tools.json` が実行可能なツールの一覧です。実行環境にプログラムが入っていることと、任意の CLI 引数・任意の GUI 操作が使えることは異なります。job の step には登録済みの操作だけを指定してください。

| 作りたいもの | 最初に選ぶツール |
|---|---|
| モデル、UV、材質、ベイク、静止画 | Blender |
| マスク、テクスチャ、画像の合成・分析 | Python + Pillow / NumPy |
| 画像の形式変換・リサイズ | ImageMagick |
| レンダーした画像列の動画化・変換 | FFmpeg |
| 対応形式からの Krita CLI 書き出し | Krita CLI |
| ノードグラフからPBRテクスチャ生成 | Material Maker |

KritaはCLI書き出しに対応します。Material Makerは `.ptex` からBlender向けPBR画像を書き出します。具体例は [`MATERIAL_MAKER.md`](MATERIAL_MAKER.md) を参照してください。ゲーム制作の機能は現在の対象外です。

## 呼び出し形式

| tool | operation | 指定するもの |
|---|---|---|
| `blender` | 指定しない | job と同じディレクトリからの `script`、必要なら `params`、`source_blend`、`preview` |
| `python` | 指定しない | job と同じディレクトリからの `script`、必要なら `params` |
| `imagemagick` | `convert` | `params.input`、`params.output`、任意の `quality` |
| `imagemagick` | `resize` | `input`、`output`、`width`、`height`、任意の `quality` |
| `ffmpeg` | `encode` | `input`、`output`、任意の `fps`、`crf`、`width` |
| `ffmpeg` | `thumbnail` | `input`、`output`、任意の `time_seconds`、`width` |
| `krita` | `export` | `input`、`output` |
| `material_maker` | `export` | `input`（`.ptex`）、`output`（ファイル名の接頭辞）、任意の必須出力 `maps` |

script は `PARAMS`、`INPUT_DIR`、`OUTPUT_DIR`、`WORKSPACE_DIR` を使います。入力パスは `input/` または `workspace/`、外部ツールの出力パスは現在の step の出力ディレクトリからの相対パスです。通常の工程出力は `workspace/output/<step_id>/` 以下にあります。任意の CLI オプションや shell command を job に渡すことはできません。詳細なスクリプト API は [`../runtime/README.md`](../runtime/README.md) を参照してください。

## step の組み合わせ

画像処理でテクスチャやマスクを生成し、後続の Blender step がそれを取り込めます。各 step の必要な出力を明示し、後続工程が読める形で保存します。

Blender では、script が正常終了しても保存・プレビュー・再読込の検証に時間がかかります。長時間のベイクやレンダーを一つの巨大な step に詰めず、途中で編集可能なデータを保存してください。

`scene.unit_settings.system = 'METRIC'` は単位系の設定として利用できます。寸法表示の設定であり、設定しただけでモデルの頂点座標が縮尺変更されるわけではありません。必要な寸法は brief と実際のモデルのサイズで管理します。

## 新しいツールを追加する

1. GUI に依存しない必要な操作と、入力・出力形式を定義する。
2. 実行環境へバージョンを管理した依存ソフトを追加する。
3. `tools.json` と runner の双方で対応する操作・引数・パス検査を追加する。
4. 失敗・timeout・出力不足を検出し、共通のログと manifest に記録する。
5. ネットワークなし・認証情報なしの制作コンテナで実行できることを確認する。
6. 小さな実入力で smoke test を行い、出力と再開を確認する。
7. runtime を再構築し、使い方とサンプルを更新する。

ツールを追加したら開始プロンプトを増やすのではなく、同じ `tools.json` を読んで選べる状態にします。存在しない操作や未検証の操作を、利用可能一覧へ先に載せないでください。

## 実行環境の更新

既定の runtime tag は `runtime-v2` です。タグは更新可能ですが、runner は各実行に実際の image digest を記録します。完全に同じ条件を必要とする再制作では、その digest と script・入力・設定も揃える必要があります。

新しい Blender のバージョンで既存の `.blend` を開けるか、書き出したファイルを戻せるかは別途確認してください。最新版という理由だけで制作途中の環境を更新せず、サンプルと既存成果物で動作を確かめます。
