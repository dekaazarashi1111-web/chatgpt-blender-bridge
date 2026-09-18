# build-v001 実画像レビュー — changes_requested

Source: `fa62aa2422961ed324297bf23440c3cbb493282f`。
Run: https://github.com/dekaazarashi1111-web/chatgpt-blender-bridge/actions/runs/35372299694
surfaces/model/lookdev/packageすべてexit0。2026-09-18T17:06:27Z開始、17:11:18Z終了。Actionsの制作・Release readback・host/review artifact保存の成功とworkspace-stateのneeds_reviewを照合した。

## 技術検証
Blender4.0.2。108 objects、410210 mesh vertices、寸法2.498×0.830×2.594m、18歯。UV／材質欠落なし。modelとlookdevの実保存後再読込pass、missing_external_files=[]。Cycles CPU、denoising=False、768px/72samplesで7方向画像を生成した。実ログにError/Tracebackは認めなかった。

review artifact10557934747を実際に取得、SHA-256 `a8415d5b4530ba738b341b6d0908f3c510ba2df6f2120b4947ace529059a5319` と一致。
host artifact10558039651を取得、SHA-256 `7c4661ea7aedbc04da7a150553cc0fc880a8f3ff4dbc418da4c95cd64d454652` と一致。
Releaseからreadbackされたmanifest実バイトのSHA-256を照合し、ダウンロードした全83出力ファイルのサイズとSHA-256がそのmanifestと一致。unpacked381421634 bytes。Release archiveはこのローカル監査で二度目のダウンロードをしていない。runner readbackがサーバーarchive digestを照合し、こちらは別形式のActions ZIPと全展開ファイルを照合した。この範囲を区別する。
監査正本: `workspace-state/workspaces/violet-rabbit-replica-20260918/evidence/build-v001/`。

## 実際に開いた画像
`output/package/previews/comparison.png`（正面・右側面・背面の上段参照／下段実レンダー）、`face.png`、`face_profile.png`、`surface.png`、`three_quarter.png`。元画像の顔・側面・耳・表面採取領域も拡大比較した。技術プレビューより、同縮尺・水平カメラの独自Cycles画像を外観判定の正本とした。

## 不一致と修正
- 全体が明るい。背面紫の診断領域RGB平均: 参照89.71/68.32/82.41、実画像126.94/102.99/118.65。腹部: 参照122.78/116.82/120.19、実画像165.62/158.45/162.73。厳密な色差指標ではないが約1stopの照明低減を試す根拠になる。
- 原寸WebPの圧縮が細部をなだらかにし、紫と淡色の模様が粘土／石の雲模様のよう。元PNGの無劣化採取を使って再構成し、過剰なbump・sheenを減らす。
- 下顎は正面でU字だが側面では斜めの細棒になり、奥行きのあるC字の顎になっていない。暗い口内も袋のように後方へ突出。厚い曲面の側板と前顎に作り直す。
- 側面で鼻が浮き、中央の口吻線も表面から離れる。鼻を口吻へ埋め、中央線を実メッシュへray-conformする。
- 後頭部の奥行きが大きい。輪郭の前後を修正する。歯の間隔と大きさ、上歯の露出も抑える。
- 耳が長い楕円／葉状で、側面がまっすぐな板。平行に近い側辺、丸い頭頂、厚み、前方への傾き、実際の深い内耳溝へ直す。
- 腹当て上部と蝶ネクタイが胴にめり込みギザギザ。解析輪郭ではなく実際のsubdivided胴表面へ合わせる。
- 肩の隙間と金属が明るく目立つ。cuffの位置を調整し金属を暗くする。欠損の境界が階段状なので該当2部品だけ高密度化する。
- 爪先が独立した球列で足首との隙間が大きい。一体の靴形状と丸みのある爪先キャップへ直す。

全高、Tポーズ幅、胴／脚の大まかな比率、分割構造は次版の基礎として保持する。全体生成や入力検証を理由なくやり直さず、変更箇所の検査と外観レビューを行う。

## 有効な保存地点
release_tag: `creative-violet-rabbit-replica-20260918-build-v001-35372299694-1-4`
archive_sha256: `3983aa75878c17d00535d3c9dda4d9992a2a5f4ee5dc28cc5548225ef0a6502b`
manifest_sha256: `cecd13eb98bb4a9fc8e435de844673af67d9d05607a7bb9964c5de4f80fe33d2`
archive bytes215014399。再開scene: `workspace/resume/output/lookdev/model.blend`。
元lookdev/model.blend SHA-256 `57d778b0af34131a39125bfeefd18cef84a715728470b2e863797fb885c58342`。
