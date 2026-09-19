# form-v003 — 実画像レビュー / changes requested

2026-09-19。対象source `0aa4a5c068c925266e536b582a329bd273ceccf1`、Actions https://github.com/dekaazarashi1111-web/chatgpt-blender-bridge/actions/runs/35427795287 attempt 1。3工程exit 0、実Actionsの全step successを確認。

## 保存・検証の根拠
最終Release `creative-rabbit-geometry-20260918-form-v003-35427795287-1-3`。archive SHA256 `2f3aae4e8f79ccb4e16abcfc618c9d6adb0d53d4ff225a23cf84f9b99d525cf5`、manifest SHA256 `dccba482459774e15e1dac8250b298778acee37937da4bc901b7217019efe74a`。
レビューartifact 10579643025を実ダウンロード: 124748753 bytes、ZIP SHA256 `84658674e79627e560de393b9e2b6e62b0c6772380c4ad18d4097cb7aad30fbd` はAPI digestと一致。host artifact 10579702897: 13317 bytes、SHA256 `086dddf27353c98fd0eb579142b4dc25d1d1517e690db5189dd91564da7b7deb` も一致。
host内のRelease manifest実バイトhashを上記と照合。readback.json pass: 66ファイルを停止後出力と照合、Release archive 116917907 bytesとserver digestを確認。この監査でarchive本体を再ダウンロードしたわけではない。
`output/model/model.blend` 86647456 bytes、SHA256 `4a22745761274f797c9a8f10766d653cd1196ef249bd940b98ee60244a5e6c1f`。Blender4.0.2の実model/renderログと両validation.jsonで再読込pass、外部依存欠落なし。geometry_audit pass、89 geometry objects、1017987 vertices、1016767 polygons、外形2.129235m幅×2.206972m高。改修した頭・手・耳は境界辺/非多様体辺0。13画像のfrustum検査pass。

## 開いた実画像
同尺度reference_comparison.jpgのfront/right/back、head_front/right/three_quarter/uniform_clay、feet_detail/uniform_clay、hand_detail、ears_detail、全身three_quarter/front_uniform_clayを開いた。原参照の顔三方向と手足・破損部の拡大も比較した。比較表の3方向は見たが、各1200px正投影PNGをすべて個別に開いたとは主張しない。

## 判定
**まだ造形未受入。** C字の側面顎、連続した指、長い耳溝、丸い耳先、全体幅は改善。単に工程が成功しただけで完成とはしない。

1. 頬の上部に尖った三日月状の突起ができた。jaw tubeの始端面が頭の内部に埋まっていないのが原因。閉じたmeshでも、露出した断面は参照と違う。始端を頭の内部へ延長して滑らかに融合する。
2. 下歯列の奥に背景が見える。既存の小さな球形baffleでは足りない。色塗りで隠さず、開口を保った実形状の口内壁・底を加える。
3. 足の前部が爪状の細い突起に見える。toe domeだけでなく、長すぎる足本体がドームの大部分を覆うことが原因。足本体の前端を後退させ、幅広く低い爪先が足の前方輪郭を作るようにする。
4. 胴肩に水平な帯状段差、四肢に箱状の輪郭が残る。既存を無条件で作り直すのではなく、この版の実画像で認めた曲率と断面の問題だけを修正する。
5. 欠損縁が鋸歯状。参照の上腕欠損は肩側が主で、全面の均等な鋸歯ではない。大腿の前・後面も原画像の位置と大まかな輪郭へ合わせる。細かな汚れは形状化しない。
6. 親指に二つの球状の膨らみ、耳の内縁に細かなvoxel由来の揺れ、蝶ネクタイに硬い折り紙状の面が残る。局所修正する。

## 次
新規form-v004で上記snapshotから継続。v003を再投入/上書きしない。モデルの成功を持ち越してv004を品質合格にしない。体の比率、ジョイント、歯、鼻、ひげ等の変更不要部位は保持し、改修範囲に応じて再検証する。テクスチャ・最終UV・リグは今回行わない。
