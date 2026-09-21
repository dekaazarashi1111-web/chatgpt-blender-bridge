# 進捗・再開入口

作品ID `folded-rabbit-finish-20260921`。2026-09-21の造形のみの仕上げ依頼。新保存先へ旧folded-rabbit-geometry-20260919/form-v006の編集可能な実データを継承する。

## 現在
intake-v001の入力/実装を準備中。job.jsonはまだ投入していない。品質合格も新しい形状改良も未実施。継承元の実Actionsは完了、needs_review。正確な親snapshotはDECISIONS.mdに記録。

## 次
入力とscriptを保存・確認してからv2 jobを追加。hash検証付き親Releaseのimport、自己完結保存、軽量の実画像・検証データを取得する。大容量artifact取得後のローカル実行タイムアウトがあり、画像を見たという虚偽の判定をしない。プレビューを開けたら参照と比較し、必要な形だけを新job IDで修正する。テクスチャへ進めない。

新規job投入後はworkspace-state/workspaces/folded-rabbit-finish-20260921/state.jsonと実Actionsを先に照合し、実行中なら重複投入しない。失敗/中断ならdocs/RESUME.mdに従う。同じprojectの最新snapshotを復元し、元のimportを不要にやり直さない。
