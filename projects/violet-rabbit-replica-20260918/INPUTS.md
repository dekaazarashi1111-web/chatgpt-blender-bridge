# 参考画像の来歴と実バイト確認

## 全体参照
添付PNG: `ChatGPT Image 2026年9月18日 00_50_08(6).png`。
1887870 bytes、2048×682 RGBA、SHA-256 `01b4c6f7a2cceb66f2530bcb9d0ea8c73d55d74ce72d8e2160936e545256ccd6`。
このセッションで実ファイルを読み、PillowでRGB→WebP quality=75/method=6、リサイズなしで変換。結果22988 bytes、SHA-256 `c878b9f1522a412c8b1174333ac456939307f3e048aea2b86120ef388d5aeaf0`、Git blob SHA-1 `2241a88e9affb64e14f8be8c78e6b79e82621c6a`。
同一バイトの既存blobを本作品の `inputs/reference.webp` に保存した。生成代替画像ではなく、同じ添付画像の実画素から変換した原寸参照コピー。ただし非可逆圧縮であり、元PNG全体のバイト列そのものはGitHubに保存済みではない。

## refine-v002用の無劣化の表面採取
v001の実画像で圧縮由来の模様のぼけを認めたため、添付の元PNGから直接小領域を切り出し、RGB画素をlossless WebPで保存。全体参照WebPを拡大したものではない。元PNG cropとの全画素一致、バイトSHA-256とアップロード先Git blob SHAを照合した。座標は左上原点の [left,top,right,bottom]。

| ファイル | 元PNG範囲 | 画素数 | bytes | SHA-256 | Git blob SHA-1 |
|---|---|---|---:|---|---|
| purple_lossless.webp | [1620,328,1668,376] | 48×48 | 2306 | 40153af37914113d5c67d6cfb55236ef05ae19a4cbf945500d35b1110fd2f85e | d36ee033bc175aaea71462477c013eefc5e9cabc |
| pale_lossless.webp | [378,365,426,413] | 48×48 | 2798 | f13651d417ab46e31c5ad9f3220ae1d3904995fc7ad6375f73cadf72075bef79 | b5140188c575b002d5225d35c20fa92084d6d505 |
| inner_lossless.webp | [370,69,383,125] | 13×56 | 812 | 80d0d6896c6da30b4e5c8ce4115612b572b684e9758f922b17ec71c0bc0b4879 | 6a0991853df5a168d87668715e2376659ac77ba4 |

すべて `projects/violet-rabbit-replica-20260918/inputs/` に保存。ジョブ入力はこのパス、targetはbasename、上表のsha256とする。参照と無劣化採取ファイルは出力にも残す。

## 材質再構成の限界
2Kは出力マップ寸法であり、元の実効解像度が2Kになったわけではない。模様は採取画像のminimum-error quiltingで再構成し、微細なnapは新規合成。大まかな色調は広い参照領域で正規化する。補助の投影マップは元画像の陰影を含むため、真の元アルベド／元UVテクスチャを回収したとは呼ばない。材質別のalpha maskで背景・ボタン・蝶ネクタイの色漏れを抑え、投影の強さはBlender上で編集可能。
