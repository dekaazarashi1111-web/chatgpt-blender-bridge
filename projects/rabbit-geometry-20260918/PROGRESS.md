# 進捗 / 再開ポイント

## 2026-09-19: form-v003 実行・保存済み、実画像で修正要求
ユーザー依頼は造形のみ。テクスチャ、最終UV、リグは未着手。
開始時main `18a05d7d2de20618c9002db243340fd685f37089` の開始指示・現行実装・schema・説明を確認。適用AGENTS.mdはtree内に検出なし。shell DNSは失敗するがGitHub接続のcommit/non-force main更新、Actions実行、artifact downloadは実利用できた。

v002を再投入せず実画像レビューし、form-v003を実行した。全3工程、保存後の実再読込、Release読戻しが成功。**造形は完成ではない。** reviews/form-v003.md/.jsonに対象版の実画像評価と次の修正を保存。form-v003は停止済み、重複実行しない。

## 現在の有効な保存地点
job `form-v003` / source `0aa4a5c068c925266e536b582a329bd273ceccf1`
Actions https://github.com/dekaazarashi1111-web/chatgpt-blender-bridge/actions/runs/35427795287
Release `creative-rabbit-geometry-20260918-form-v003-35427795287-1-3`
archive SHA256 `2f3aae4e8f79ccb4e16abcfc618c9d6adb0d53d4ff225a23cf84f9b99d525cf5`
manifest SHA256 `dccba482459774e15e1dac8250b298778acee37937da4bc901b7217019efe74a`
source_blend `workspace/resume/output/model/model.blend`
model SHA256 `4a22745761274f797c9a8f10766d653cd1196ef249bd940b98ee60244a5e6c1f`
制作元base_geometry_source.py、parent_form-v002_source.py、geometry_source.pyとreference.webpも現在output内に保存。復元時はmanifestに従う。

## 次の作業
新規form-v004を準備する。このメモ時点では未投入。まず最新state/Actionsを照合。
修正対象: 頬のtube端部を内部で接続、口内の壁と底を実形状で閉じる、足本体と爪先の重なり改善、肩/四肢の曲率、欠損輪郭、親指、耳縁、蝶ネクタイ。鼻・歯・ひげ・内部ジョイント等の不要な再制作はしない。
スクリプト/入力を先行保存しjob.jsonは最後に追加。実行後は対象版の画像と自動検証、Release/manifestを確認し、レビューまでcommitする。

## 失敗した方法
reviews/form-v001〜v003.mdに記録。過大なmouth cutter、C1断面補間の陰影帯、露出したtube始端、爪先を覆う足本体、鋸歯状の欠損が不適切だった。単純な形状部品の有無、ポリゴン数や画像IoUを忠実度や完成率と呼ばない。
