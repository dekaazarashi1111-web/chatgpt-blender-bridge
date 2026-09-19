# 進捗 / folded-rabbit-geometry-20260919

対象は折れ耳・腕を下ろしたオリジナルキャラクター。2026-09-19追加依頼は造形の仕上げのみ。テクスチャ・UV仕上げ・リグは別セッション。旧rabbit-geometry-20260918/T-poseやstudio-smokeを対象と取り違えない。

## 最新実行 — form-v006 / running
source `a2c964a566719aaa8364947a1ecddf9c0a35165b`。
Actions https://github.com/dekaazarashi1111-web/chatgpt-blender-bridge/actions/runs/35439434026 attempt1。11:11 UTCにpush起動/in_progressを実確認。対応するstate/Actionsを追跡し、重複投入しない。
ソース保存commit `342b29979a329b091ee8e3142f14387d3e811807` の全5スクリプトのGit blob SHA/bytesをローカルで検査したファイルと照合した後、job.jsonを最後に追加。総予算18000秒、model5400/render7200/package900。既存の検証済みruntimeを利用し、不要な再buildはしない。

v005実画像の不合格部分を修正する顔のみの版。角丸box口元を凸曲面の左右ローブと連続鼻梁へ置換。頬の膨らみを頭部へ統合し、実曲面に沿う薄い下側カバーをBooleanによる浅い接合溝へ収める。丸い小鼻と中央溝、目の位置を微調整。胴・改善済み肩腕と指・骨盤・脚足・耳・顎・歯・蝶ネクタイ・尾はfingerprintで保持し再制作しない。
影響のない耳、足detail/clay、手detailの4画像はhashと対象geometry不変証拠で再利用し、9枚の影響する全身/頭部画像を新規描画。頭部4ビューの部分記録も先にcheckpointする。model工程の出力へ親の描画cache/manifest/sourceをコピーし、model-only保存地点から先の描画依存も残す。正確な頭部meshのNumPy書出しも.blendと共に保存する。
新しいBlender実行、保存、造形検査、実画像レビューの結果はまだ未確認。ローカルNumPyの同解像度閉形状検査、頬カバーの閉辺/有限値、構文/補助関数hash照合は成功。初期ローカルsource assemblerの区切り文字誤りと未実行package案の変数名は投入前に検出・修正した。VTKのローカル形状試作はBlender保存シーンの実画像ではなく、完成証拠に扱わない。

## 最新の実取得・検証済み保存地点 — form-v005
source `464b693576b7ef291ab475149d3b9932e2014359`。
Actions https://github.com/dekaazarashi1111-web/chatgpt-blender-bridge/actions/runs/35437918879 attempt1。10:56:57 UTCにmodel/render/package全exit0で完了。publication_errors=[]。
Release `creative-folded-rabbit-geometry-20260919-form-v005-35437918879-1-3`
- archive262359909 bytes、SHA256 `88ddbc0eb62eb3805c2b1d283699bdff3b7ba9d7fc1c51a824b8c1454cc73f17`
- manifestSHA256 `a9e70d2357c836ecc733efac24d3cb625809595b20f6049bf551ab1c8929f199`
- 復元model `workspace/resume/output/model/model.blend`、185443584 bytes、SHA256 `1b03ae315e87e6243b57349532e954fe71f9a375cdc9c02d240a8d136e3daf44`
- 納品model `output/package/folded_rabbit_geometry.blend`、185448184 bytes、SHA256 `afe1a24c860d3fc2f42b61c8027eed68025eedd05808edb965151c633bdcd6db`

review ZIP10583151870 / host ZIP10583321690の実バイトhash、CI読戻しmanifest実バイトhash、manifest全105ファイルのsize/SHA256を独立照合。不一致/欠落0。両CI再読込、外部依存、全mesh閉形状、有限座標、必須部品/口元group、実寸、no image-texture nodes、13画像/frustum、再利用3画像hash/geometry保持は合格。
実際の参照比較、原寸head_front、変更10ビューを原寸参考画像3枚と比較。頭頂の段差と指くびれは改善したが、口元の板状形、浮いた花弁状頬、口元と眼窩の微細うねりが残るため `changes_requested`。source/archive固定レビューを `reviews/form-v005.json/.md` に保存（commit0dbd6bf837a27981d8532747a6b351cd7e8bcd7e）。完成ではない。
最終Release TAR自体をこのセッションが再取得したという意味ではない。実際に独立照合したものはActionsの完全ZIP/出力と、CIがReleaseから読戻したmanifest/server archive digest。v005 model-step単独checkpointは.blend自体有効だが、既存cache再利用rendererの継続にはv004親cacheも必要だった。この不足をv006で解消する。次版の親はv005の最終snapshotを使う。

## 以前の保存地点・レビュー
v004 sourcee67bb2848173b8c31f4b28e2b054999ed3c951de、run35433907363、最終Release `creative-folded-rabbit-geometry-20260919-form-v004-35433907363-1-3`、archive079b97150104e94be776e3396ae06b112f416a5680f8d45b919d4030ba4f3be2、manifest6dddb80268cde1edb1c508b228cc1314fc9c48b21b1295d1d6e0b6cb8a357184。全99出力独立hash一致、技術検査成功、実画像レビューchanges_requested。詳細 `reviews/form-v004.*`。
v003以前の経緯・失敗した形・保存地点は各reviews、job PLAN、Git履歴に保存済み。受入済み元作品importや影響のない部品の再作成は行わない。

## 再開時の最初の作業
main最新HEADの指示とv006のworkspace-state/各job/Actions/Release manifestを照合。runningなら同runを待ち重複投入しない。完了なら両artifact、再読込、形状監査、13ビュー（9新規/4継承）、cache依存、頭部meshを書戻し照合し、原寸参考画像と実画像比較する。実行成功だけで完成にしない。必要なら新IDで修正し、対象source/archive固定レビューをcommitして状態反映する。失敗はdocs/RESUME.mdと公開済み工程snapshotから再開する。

## 原寸入力と実行経路
Libraryから1086x1448元PNG3枚を回収し、INPUTS.md記載の元SHA256との一致を確認した。原寸は今回の視覚比較に使用。GitHub/Release/blendに保存された300x400 WebPは同じ画像の実画素派生であり生成代替画像ではない。各jobへ復元/持越し。原寸PNG自体はGitHubへ未アップロードで、ローカルのみをGitHub保存済みとは呼ばない。
開始HEAD9160fcd1aaa5fabec4cbc040e0d60750a42990d1のexecutor指示、README、contract、tools、v2 schema/sample、INPUTS/RESUME、runtime説明、Actions/review実装を確認。再帰treeに適用AGENTS.md該当なし。シェルgit/Blender/PyPIはDNS失敗だが、接続済みGitHub APIのmain非force更新とpushイベント実行が成功している。
