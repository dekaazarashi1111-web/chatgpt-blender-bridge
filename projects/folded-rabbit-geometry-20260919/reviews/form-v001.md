# form-v001 実画像レビュー — changes requested

対象project: folded-rabbit-geometry-20260919。source `0eb25f886539d7aa9b4b37b60337a46c75ebd086`、Actions https://github.com/dekaazarashi1111-web/chatgpt-blender-bridge/actions/runs/35429889918 、attempt1。

## 実行と永続保存
全4工程 exit0、Actions prepare/create成功。state=needs_review、publication_errors=[]。
最終Release `creative-folded-rabbit-geometry-20260919-form-v001-35429889918-1-4`。
archive SHA256 `d22896786f350e02e96e07920797a619dbfc076d85f855bcb1352329da33ec77`、129072133 bytes。
manifest SHA256 `eda577fc0f024e9259fff0eae2f747db2c0a8b4c243903e0769c1f9595316807`。

review artifact10580601350（137138405 bytes、SHA256603cf31eb058ae7548a2cd1c4557fa57aa717595f2bd4b87e5e5b53a4b14a3a1）とhost artifact10580381749（11656 bytes、SHA25665bb3a8c8468121277842935125da0d6541dae0382efd5a475f1550de2d200da）を実取得。API digest、Releaseから読戻されたmanifestの実バイトhash、全80出力ファイルのsize/hashを照合済み。CI readbackもpass。今回の監査で最終Release archiveそのものを再ダウンロードしたとは主張しない。

import_evidenceは親Release archive116917907bytesとmanifestを実ダウンロードし66ファイルをhash検証済み。親を新規projectへ明示importしたもので、同一project限定resumeを変更していない。この受入済みimport工程を次版で繰り返さない。

model/render両validation pass、missing_external_files=[]。92形状オブジェクト、811470頂点、811926ポリゴン。主要7外装のnonmanifold/boundary edgeは0。必須部品数、有限座標、画像テクスチャ不使用を検査済み。実高さ2.23085m、幅1.03161m。

## 実際に比較したもの
geometry_contact_sheet.jpg（全身正面/側面/背面/斜め、頭部斜めと単色）、head_right.png、hand_detail.png、feet_uniform_clay.png、ears_detail.pngを開いた。加えて原寸の新しいPNG3枚から高さを揃えた正面/側面比較を作成して開き、元画像の顔の正面・側面拡大も再確認した。画像生成による代替プレビューではない。

## 不合格の理由と次の修正
- 折れ耳と腕が角張った箱になりすぎ。参照はもっと丸く膨らんだ外装。耳先の灰色の矩形板が浮いており、参照にない不要な段差。耳の全高も約3cm過大、側面では折れた先端の前方突出が不足。
- 眼窩の平面リングと目が顔面より前へ出てゴーグルに見える。リングを撤去し、厚く丸い実際の眼窩に眼球を沈める。
- 鼻梁から口元が連続せず、二つの小さい箱が顔に貼り付く形になっている。頭部前面とマズルの断面を一体的に修正する。鼻の前方突出も減らす。
- 頬が球状のボールに見える。参照の下端が絞れた丸い頬パッドへ変更。上歯の一部が浮遊球状に見えるため、口腔/歯列の位置と形を修正。
- 肩球の露出が過大、上腕が短く見える。上腕の上端を肩へ食い込ませ、前腕を含め曲面のある外装にする。
- 骨盤と大腿の融合部に不自然な線状盛上り、膝の見える隙間が大きい。自然な一続きの外装へ修正。
- 手掌が箱状で、指の根元に角張った露出端面がある。丸みと接続を修正。爪先は卵の半分のように尖りすぎで、参照の丸い角を持つ太い爪先へ変更。
- 蝶ネクタイの三角形面が平坦。実際の厚みと滑らかな折れ・ひだへ変更。

全体の姿勢/幅/部位構成は今回の参照に沿っているが、造形の受入はまだ行わない。概算silhouette IoU（正面0.909、側面0.802、背面0.904）は閾値マスクと高さ合わせに依存し、完全再現率ではない。

## 次の保存地点
同一projectの上記最終snapshotから `workspace/resume/output/model/model.blend` を読み、新ID form-v002 で修正。元の入力・造形ソース・依存を新出力へ持ち越す。テクスチャ/UV仕上げ/リグは行わない。
