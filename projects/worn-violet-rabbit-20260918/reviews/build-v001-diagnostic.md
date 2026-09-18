# build-v001 実行・初期画像レビュー

## 対象と結果
Source `397cbc69c21c323727da2e3e6163ce23586d357d`。
Run https://github.com/dekaazarashi1111-web/chatgpt-blender-bridge/actions/runs/35364229702
2026-09-18T15:44:44Z開始、15:47:08Z終了。textures/modelはexit0、presentationはexit1、packageは未実行。stateとActions完了failureを照合。失敗した実行全体を合格とはしない。

## 実ファイルで確認
Actions artifact ID `10554994139` をダウンロードしZIP SHA-256 `d69acd7028ac6d2eeeef31a79f3d7c5d0e5a5608a258fff37575697236cc9c2d` を照合。実際の model.blend、画像、テクスチャ、tool_report.json、geometry_validation.json が存在。
Blender 4.0.2で保存後の再読込pass、missing_external_files=[]、scene objects161。造形検査は有限頂点149845、renderable objects155、寸法2.492266 x 0.733590 x 2.599000m、歯18、材質なし0。これらは技術検査として確認済み。

## 開いて比較した画像
`output/model/previews/front.png`, `right.png`, `back.png`, `three_quarter.png`（いずれも実際の512px自動レンダー）。
参考のTポーズ、二本の耳、蝶ネクタイ、二つのボタン、淡色腹部、分割四肢、尾、口と歯列の存在は確認できる。ただし外観受入は保留。
- 自動プレビューは元のライトに追加ライトが重なり、紫と淡色部分が参考よりかなり明るい。色の最終調整は水平・同縮尺の独自Cycles画像を見て行う。
- 黒目が前方へ突出し、光点が多くて参考より人形的に見える。目周囲と口吻のつながりを再確認する。
- 上腕・腿の損傷が四角いパネル穴に見える。参考の不規則な裂け方へ調整候補。
- 側面と斜めで耳の板状感、口吻の球状の継ぎ合わせが目立つ。参考に近い量感へ修正候補。
- 表面のまだらは出ているが、明度と模様の強さ・尺度はまだ一致判定していない。

## 実際の失敗原因
presentation/render.pyが `scene.cycles.use_denoising=True` でレンダーした際、ログに `Build without OpenImageDenoiser` / `No device available to denoise on`。CPU Cyclesのノイズ除去機能がこのUbuntu Blenderビルドにない。造形生成の失敗ではない。
次のrender-v002ではdenoising=False、128samples、adaptive_threshold=.02とし、既存保存モデルからレンダーだけを再開する。関係のないツール環境の再ビルドや受入済みマップ生成の再実行は不要。

## 選んだ有効な再開地点
失敗前のモデル完了snapshot（Release metadataのsize/digestとworkspace-stateを照合済み）。
- release_tag: `creative-worn-violet-rabbit-20260918-build-v001-35364229702-1-2`
- project_id: `worn-violet-rabbit-20260918`
- job_id: `build-v001`
- archive_sha256: `ef849df8211ccb60e4fc64a3899384720f1e31d428575e432d8b1a4e2da30ef8`
- manifest_sha256: `a05be2b321e5345acac7f6905dce8fb63d4a33d702c92139ec580ac6da929dc1`
- archive asset572932788、83610295bytes
- manifest asset572932856、5220bytes
- model relative path: `output/model/model.blend`

既存の復元機構がmanifest/archive/全ファイルを検証してから復元する。新しいreadback evidence工程でRelease manifestの実バイトを再取得し、停止済みの各ファイルと照合してworkspace-state/evidenceにも保存する。Release自体は上書きしない。

## 次の判定
render-v002の比較画像で造形・目・損傷・紫の明度・まだら模様を確認し、必要なら新しいjob IDで部分修正する。ユーザーの忠実再現要求を満たした最終版と現時点で主張しない。
