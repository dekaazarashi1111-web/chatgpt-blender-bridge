# form-v002 — 2026-09-19 実画像レビュー / changes requested

対象source `0fdebb95a32118f8bfa2e75da4ee0ecb2de23170`、Actions https://github.com/dekaazarashi1111-web/chatgpt-blender-bridge/actions/runs/35390326287 、attempt 1。開始時のmain `18a05d7d2de20618c9002db243340fd685f37089`。古いPROGRESS.mdの未投入表記に反して、v002は完了していた。再投入していない。

## 保存と技術検証
全3工程exit 0、Actions completed/success。workspace-stateの最新snapshotは `creative-rabbit-geometry-20260918-form-v002-35390326287-1-3`。archive SHA256 `93dbd6936c126531da994e2ac3905af380b84f362275e5064f33d4ebf6cdb123`、manifest SHA256 `d61ae5dce72b2b3480183cc76a8387ede3804026d3ec91ec18c2a1bb5c89f1b1`。

接続のdownload_workflow_artifactでレビューZIP 10566181633を実取得。69079974 bytes、SHA256 `dbf2e8bf1968b5b031ec15db340c336b155f0389cd1698352646abd368125b6e` はAPI digestと一致。host ZIP 10566091703は12606 bytes、SHA256 `a264d4e756854d09f61193e36167f91ed38d71bed04d033c58f06df78695bdf7`。収録されたRelease manifest実バイトのhashも上記と一致。CI読戻し記録ではRelease manifestを再取得し57ファイルとarchiveのserver digest/sizeを照合済み。この監査でRelease archive本体を再ダウンロードしたとは主張しない。

`output/model/model.blend` は61550876 bytes、SHA256 `f028acd02a8dd1ddd57f64d260e75fb50382151c72668cb1ea0fec39bc8f1f4f`。Blender4.0.2のmodel/renderログ、両validation.json、geometry_audit.jsonを確認。両再読込pass、missing_external_files=[]。91 geometry objects、553737 vertices、550105 polygons。保存済み技術検証を意味なく再実行しない。

## 実際に開いた画像
reference_comparison.jpg（同尺度front/right/back）、head_three_quarter.png、head_right.png、hand_detail.png、feet_detail.png。今回取得した添付相当の三面図と補助スクリーンショットも開き、三面図の顔3方向と側面座標グリッドを拡大して照合。未閲覧の別画像を閲覧済みとは扱わない。

## 判定と次の修正
**造形未受入。** 全体尺度、Tポーズ、保存、顔の突出量低減、カメラの切れ改善は前進。ただし忠実度目標にはまだ不足。

- 眼窩が鋭い円筒穴に見える。参照の少し厚く丸い縁と眉への滑らかなつながりを作る。眼球を穴の奥に消さない。
- 下顎側面がまだ直線的な斜めの棒。参照では上端x990/y206から外側x1018/y229へ後方に回り込み、下端x950/y272へ曲がる厚いC字。顎を切断する大きなcutterと単純sinの掃引を変更する。
- 頭部、耳、爪先の輪状の陰影段差と終端の平面をなくす。単なるポリゴン数増加ではなく、曲率と端部の接線を改善する。
- 指の付け根に急な円筒キャップ状の境界、親指に球状の継ぎ目がある。根元を掌の内部からつなぐ連続曲面にする。
- 爪先が四角い棒状で、端面に同心状の段差がある。丸いドームと平らな接地面、足本体に馴染む後端へ変更する。
- 耳の細長い溝は底に厚い横桟を残しすぎ。参照の下端まで伸びるくぼみと柔らかな丸い頂部へ調整する。
- 新しい形状をその版の全身・近接・単色クレイで再評価する。実行成功や概算silhouette IoUを『完全再現率』に言い換えない。

## 今回の範囲
ユーザーの追加指示は造形のみ。UV仕上げ、テクスチャ、Material Maker、リグは開始しない。見えない内部と断面は推定であることを維持する。次の新規IDはform-v003。v002の有効snapshotから復元し、未変更部位と参照の依存ファイルを現在の出力にも保存する。
