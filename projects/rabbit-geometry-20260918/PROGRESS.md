# 進捗 / 再開ポイント

## form-v001 実行済み・造形修正要求
Source: `71b31cce0136ea645abf692bdfb41f3162136796`。
Actions: https://github.com/dekaazarashi1111-web/chatgpt-blender-bridge/actions/runs/35388084369
全3工程success。Blender4.0.2。保存sceneの実再読込pass、依存欠落なし、45ファイルのRelease manifest読戻し照合pass。

**完成扱いしない。** 実際にダウンロードした全身三面、頭部正面/側面/斜め/単色クレイを確認し、眼窩、顎の厚みと突出量、耳の厚みと端部、指と爪先、近接カメラの切れを修正要求として記録した。`reviews/form-v001.md` と pinned JSON を参照。

## 保存先
Release tag `creative-rabbit-geometry-20260918-form-v001-35388084369-1-3`。
archive SHA-256 `c4653aff5afb32c80af011d97d6b201bc969d5bd5145e8d2ae40f9c3a14bb61f`。
manifest SHA-256 `0f4a1c5df7f382d84ca1715eec125f6bd99c0dade7e665591b6b399131bd260a`。
再開するモデル: `workspace/resume/output/model/model.blend`。ソース、参照コピー、プレビュー、検査結果もsnapshotにある。

## 次の作業
新規job ID form-v002を用意し、上のsnapshotから復元して該当部位を修正する。まだv002は投入していない。実行前に現在のworkspace-state/Actionsを照合し、既にv002があれば重複投入しない。後工程のテクスチャ、UV仕上げ、リギングは今回行わない。
