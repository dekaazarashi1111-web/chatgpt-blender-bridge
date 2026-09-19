# 入力実体と出典

ユーザーが2026-09-19にこのチャットへ添付した3枚。原寸1086×1448pxのPNGは今回の視覚分析に使用した。GitHubへ保存したファイルはその実画素からPillowで300×400pxへLANCZOS縮小しWebP quality=30 method=6で符号化した比較用派生画像であり、生成代替画像ではない。原寸PNGのアップロード完了とは扱わない。

| 役割 | 保存入力 | bytes | SHA-256 |
|---|---|---:|---|
| 正面 | inputs/front.webp |4230|5bc9453676cd565de87b3d7932bd313fef6f436ad83799789f055c58697c6856|
| 側面 | inputs/side.webp |2480|e8561ec50343c90bdf84de990e2226232581f5bf74759fbd6162ec3c9755e5a2|
| 背面 | inputs/back.webp |3616|02d44e650c353453bc553179497e51519ccca1167f0c4909ac90a79089cdead8|

原寸ファイル（この時点ではGitHub未保存）:
- ChatGPT Image 2026年9月19日 16_07_53 (1).png: 2473662 bytes、SHA256 a4cd35087eab4f7366a861f6c979978f922b1142755df9fcf739dc53718886d4。
- ChatGPT Image 2026年9月19日 16_07_54 (2).png: 2462920 bytes、SHA256 f141575e4534d9715d3d9baeec31de0ef1f5251a1f7f5d473e3ec8d71a42df4c。
- ChatGPT Image 2026年9月19日 16_07_54 (3).png: 2620530 bytes、SHA256 3374bfb35690e31997e1051f631d199202fe2d5a7e9164685a3630344efd158c。

新ジョブは上の3派生画像をhash付きinputsとして明示し、出力にもコピー/packする。入力画像をテクスチャへ貼りつけることはしない。詳細は原寸の視覚分析と幾何仕様に記録する。次回テクスチャ制作で原寸画素が必要なら原寸を別途確保する。
