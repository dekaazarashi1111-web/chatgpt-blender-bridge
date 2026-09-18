# Material Maker で材質を作る

Material Maker 1.7 の公式 Linux 版を共通環境へ組み込んでいます。配布ファイルの SHA-256 と版は [`../runtime/material-maker.lock.json`](../runtime/material-maker.lock.json) に固定しています。制作中のダウンロードは不要です。

## 同じ開始プロンプトで使う

ChatGPT は `tools.json` を読み、必要なら `material_maker` の `export` を制作工程へ追加します。専用の開始プロンプトは不要です。編集する元データは Material Maker の `.ptex`（JSON形式のノードグラフ）です。

完成したジョブの書式は [`material-maker-v001`](../projects/studio-smoke/jobs/material-maker-v001/job.json) にあります。新規作成には [`terracotta.ptex`](../runtime/fixtures/material/terracotta.ptex) を参考にできます。ノード・パラメーター・接続を編集して色、模様、凹凸などを変えます。単に文章を渡すと自動生成する画像AIではなく、ChatGPT が材質グラフを作成・編集して実行する仕組みです。

## ジョブの書式

```json
{
  "id": "material",
  "tool": "material_maker",
  "operation": "export",
  "params": {
    "input": "input/material/terracotta.ptex",
    "output": "terracotta",
    "maps": ["albedo", "roughness", "metallic", "normal", "height", "ao"]
  }
}
```

これは job の `steps` に入れる1工程です。入力は通常どおり `inputs` に実ファイルと SHA-256 を登録します。前工程で作成したグラフや復元したグラフは `workspace/` 以下から指定できます。

| 項目 | 内容 |
|---|---|
| `input` | `.ptex` のパス。`input/` または `workspace/` から始める |
| `output` | 出力ファイル名の接頭辞。英数字・`_`・`-`、最大80文字 |
| `maps` | 必須とする出力。省略時は `albedo`。指定した画像が生成されなければ失敗 |

使える map 名は `albedo`、`roughness`、`metallic`、`normal`、`height`、`ao`、`emission`、`sss` です。生成するには Material ノードの対応する入力を接続してください。`maps` の指定だけでグラフに接続が追加されるわけではありません。

## 保存されるもの

`output/<step_id>/` に次のファイルを保存します。

- `source/`：元の `.ptex` と、同じフォルダーにまとめた画像などの依存ファイル。
- `<接頭辞>_albedo.png`、`_normal.png`、`_rough.exr`、`_metal.exr`、`_displace.exr`、`_occlusion.exr` など：実際に生成したテクスチャ。
- `material_report.json`：生成した map、画像サイズ、SHA-256、使用した Material Maker の版。
- `previews/albedo.png`：ChatGPTから確認しやすい縮小プレビュー。

工程終了時に通常の workspace snapshot へ保存されます。次のセッションでグラフを編集する場合も、snapshot の `source/` から続行できます。

`.ptex` と画像は専用フォルダーへまとめてください。そのフォルダー全体を保存するため、上限は4096ファイル・256MiBです。シンボリックリンクは使えません。画像ノードには `%PROJECT_PATH%/images/reference.png` のように、グラフのフォルダーを基準にしたパスを使い、実画像も同じ bundle 内へ登録します。手元の絶対パスやオンライン素材のURLは使わないでください。

## Blenderへの取り込み

後続の Blender script から共通関数を呼べます。

```python
from bridge.blender_material import load_material_maker

material = load_material_maker(
    WORKSPACE_DIR / "output/material",
    name="Terracotta",
    height_distance=0.04,
)
obj.data.materials.append(material)
checkpoint("material-ready", "Material Makerの材質を設定")
```

画像の SHA-256 を確認してから、色画像を sRGB、数値画像を Non-Color として読み込みます。Base Color・Roughness・Metallic・Normalへ接続し、AOは色へ乗算、heightはバンプとして適用します。emissionも対応します。`sss` は書き出し・読み込みまでで、用途に応じてscript側で接続してください。Blenderの保存時に画像を pack するため、保存後のモデルは元の画像パスへ依存しません。編集用 `.ptex` はsnapshot側に残ります。

## 実行条件

- 1グラフにつき Static PBR Material（または Displacement 版）を1個使用し、Blender向けに書き出します。
- 標準の出力は **2048×2048**。必要なら後続の画像処理で縮小します。1.7のCLIでは `--size` の値が書き出し関数へ渡されないため、現状その指定は公開していません。
- 描画処理は Mesa lavapipe によるCPUのVulkan計算です。複雑なノードや大量の材質は時間を使うため、工程を分けてください。
- ウィンドウ操作はXvfbで処理します。GUIでの手描きやWebライブラリの自動取得は、この操作には含みません。

公式の [CLI説明](https://github.com/RodZill4/material-maker/blob/1.7/material_maker/doc/command_line.rst)、[書き出し仕様](https://github.com/RodZill4/material-maker/blob/1.7/material_maker/doc/export.rst)、[CLI実装](https://github.com/RodZill4/material-maker/blob/1.7/parse_args.gd) を基にしています。

### CPU環境での起動互換処理

公式配布ファイルは変更せず、`runtime/material-maker-renderer.gd` を Godot の `override.cfg` で読み込みます。Material Maker 1.7 が描画デバイスの準備を待たずにシェーダーを使う競合を、初期化の完了待ちで防いでいます。また、CLIの終了時に描画スレッドを閉じ、終了待ちが止まる問題を防ぎます。描画処理は元の専用スレッドで続行します。この互換処理の SHA-256 も成果物の `material_report.json` に記録します。
