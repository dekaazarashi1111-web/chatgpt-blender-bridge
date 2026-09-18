# 参考画像の来歴と実バイト確認

添付PNG: `ChatGPT Image 2026年9月18日 00_50_08(6).png`
1887870 bytes、2048×682 RGBA、SHA-256 `01b4c6f7a2cceb66f2530bcb9d0ea8c73d55d74ce72d8e2160936e545256ccd6`。
このセッションで実ファイルを読み、PillowでRGB→WebP quality=75/method=6、リサイズなしで変換。結果22988 bytes、SHA-256 `c878b9f1522a412c8b1174333ac456939307f3e048aea2b86120ef388d5aeaf0`、Git blob SHA-1 `2241a88e9affb64e14f8be8c78e6b79e82621c6a`。

同一バイトのWebP blobが既存作品のinputsに存在することを照合し、本作品の `inputs/reference.webp` にそのblobを保存する。これは新しい生成代替画像ではなく、同じ添付画像の実画素から変換した原寸参照コピー。ただし非可逆圧縮であり、元PNGのバイト列そのものはGitHubに保存済みではない。この違いを隠さない。

Job input: path `projects/violet-rabbit-replica-20260918/inputs/reference.webp`, target `reference.webp`, sha256 `c878b9f1522a412c8b1174333ac456939307f3e048aea2b86120ef388d5aeaf0`。

参照コピーはジョブ入力としてhash検証し、出力へコピーし、Blenderにもpackする。画像由来の材質は投影された照明を元の真のアルベドと混同せず、採取範囲、元の有効解像度、処理方法を記録する。
