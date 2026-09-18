# form-v001 — 実画像レビュー: changes requested

## 対象版と実行
Source `71b31cce0136ea645abf692bdfb41f3162136796`。
Actions https://github.com/dekaazarashi1111-web/chatgpt-blender-bridge/actions/runs/35388084369 （attempt 1）。model/render/packageの3工程はexit 0、Actionsとmanifest読戻しもsuccess。Blender実版4.0.2。
最終Release `creative-rabbit-geometry-20260918-form-v001-35388084369-1-3`、archive SHA-256 `c4653aff5afb32c80af011d97d6b201bc969d5bd5145e8d2ae40f9c3a14bb61f`、manifest SHA-256 `0f4a1c5df7f382d84ca1715eec125f6bd99c0dade7e665591b6b399131bd260a`。

## 確認した証拠
レビューartifact 10564434231を接続経由で実ダウンロード。ZIP SHA-256 `476316761a92d66be74d75a8f5557bf0d37253c784413508fd8d1199d1f23fc7` はAPIのdigestと一致。実ファイルの reference_comparison.jpg（三方向全身）、head_front.png、head_right.png、head_three_quarter.png、head_uniform_clay.png を画像として開いた。元の添付三面図と拡大スクリーンショットも比較した。色付きテクスチャで欠点を隠していない。

geometry_auditは全検査pass、100 geometry objects、208876 vertices、206663 polygons、高さ2.205m、全幅2.10m。model/renderの保存ファイルは実際に再読込され、missing_external_filesは空。出力Blenderファイル `output/model/model.blend` / `output/package/rabbit_geometry.blend` は21380444 bytes、SHA-256 `289754f38674d6fa6f430beef20cffdbecee62030eceabc8bc0f2a8a930a7c92`。
workspace-stateのexact latest-manifest.jsonとreadback.jsonを読んだ。CIがReleaseからmanifest実バイトを再取得しhash検証、45ファイルを停止後の出力と照合、archiveのserver digest/sizeを照合。archive本体をこの監査で再ダウンロードしたわけではない。

## 造形の判定
**不合格、修正する。** 全身の主要ランドマークと基本的なTポーズは近いが、今回の忠実度目標にはまだ不足。

1. 眼窩の球を単純unionしたため、眼窩がゴーグルのように前へ突出し、縁が薄く鋭い。参照の顔はもっと連続したマスク状で、眉・頬に滑らかに接続する。
2. 下顎の側面が細い斜めの棒に見え、前へ出すぎている。参照の下顎先端は側面x約949–954（Y約-0.27m）、本モデルはY約-0.326m。側面の厚い頬〜顎壁と浅いC字形状を作る必要がある。
3. 鼻先も約20–25mm前に出すぎ。上マズルの長さは比較的近いが、上下歯列と顎の前後関係を修正する。
4. 耳は側面で約10mm以上薄く、先端が平らな斜め切りの棒状。幅・厚みを参照の各高さで調整し、上端を三次元的に丸める。くぼみ底のinsertが底面の後ろに隠れている点も修正する。
5. 手は連結した指ではなく円筒＋球の集合に見える。足の爪先は球が並びすぎており、輪郭・底面が参照より狭い。指間の溝を残した連続した手袋状の形、平らな底面を持つ爪先へ修正する。
6. 肩上部は約数mm〜20mm低く/細く、膝の段差と隙間は大きすぎる。胴・脚の配置は維持しつつ該当部を局所調整する。
7. 頭部右側のclose-upで鼻がフレームから切れていた。全身側面では切れない。次版のclose-upは頭だけを対象にframingし、耳/体の映り込みと頭部の切れを別々に検査する。

## 比較手法の注意
ローカルで300px/mの同一尺度にrenderをアフィン再配置し、参照上へ輪郭を重ねた。最初の自動マスク方式（外側flood-fill）は両脚の間まで埋める誤りがあり、定量評価に使わない。小穴のみを除去する方式へ修正しても、暗い関節、ひげ、微小な背景穴の誤分類が残る。マスクIoUを『再現率』『完成度』に言い換えない。修正は実際の画像と具体的な位置の比較を優先する。

## 次
form-v001を上書き/重複実行せず、新しいform-v002で最終snapshotの `output/model/model.blend` を復元。胴・内部ジョイント・損傷など再利用できる部位は保持し、顔/耳/顎/手足の修正と必要な撮り直しのみを行う。テクスチャは今回の範囲外のまま。
