# 進捗と再開入口

## 現在の作業
`refine-v003` を保存済みsceneからの部分修正版として投入した。Actions実行中を確認。まだこの版の造形・外観は未検証。重複投入しない。
- Source commit: `991e68d180c8bbf6038b298fa011f92b6490ae09`
- Job: `projects/worn-violet-rabbit-20260918/jobs/refine-v003/job.json`
- Actions: https://github.com/dekaazarashi1111-web/chatgpt-blender-bridge/actions/runs/35368608273
- Descriptor validation: https://github.com/dekaazarashi1111-web/chatgpt-blender-bridge/actions/runs/35368608269 （success確認）

## 直前の検証とレビュー
`render-v002` はcarry/presentation/package/Release readback監査が成功。7枚の1024px Cycles画像、3面図、参考比較、顔・側面・表面詳細、packed .blendを生成した。実際のファイルをダウンロードし、Releaseから再取得したmanifestと全53ファイルのsize/SHA-256を照合した。保存後の再読込pass、外部依存欠落0。
実画像を参考と比較し、明るすぎる質感、格子状の模様、幅広すぎる口吻、突出した黒目、薄い耳、大きすぎる肩の隙間、四角い損傷、腹当てと足先の輪郭を不一致として記録。`reviews/render-v002.json` の `changes_requested` がworkspace-stateへ適用されたことも確認済み。完成扱いにしない。詳細は `reviews/render-v002.md`。

## v3で変更する範囲
保存モデルから目のくぼみ／沿う顔面模様／中央の口吻と鼻／下顎の奥行き／厚い耳／肩のはまり／腹当て輪郭／不規則な裂け／丸い足先を部分修正する。変更しないモデルを全て生成し直さない。
実参考の表面画素を使い、低周波の陰影を抑え、周期境界を補正した2Kの色・粗さ・16bit高さ・法線マップを作る。元のパッチ解像度は紫92x96、淡色74x64px。追加の微細な織りと粒は生成成分であり、元作品の高解像度UVを回収したとは主張しない。crop、変換、hashはsurface_provenance.jsonに残す。
7枚の同条件比較レンダーで修正結果を見る。古いプレビューはcarry工程で除き、今回のモデルとして再掲載しない。ノイズ除去非対応は既に判明しているので、検証済みのOIDN無効設定を継承する。

## v3が復元する有効な保存地点
Release: https://github.com/dekaazarashi1111-web/chatgpt-blender-bridge/releases/tag/creative-worn-violet-rabbit-20260918-render-v002-35365556050-1-3
- project_id: `worn-violet-rabbit-20260918`
- job_id: `render-v002`
- archive_sha256: `210366034138de2015d8d5d7877cb336b9fb90b8ec02e9209226222010540e0f`
- manifest_sha256: `eac9e6554fff91dc88200495e7953bcbc707d47353eaedb0787012635957ba3b`
- source_blend: `workspace/resume/output/presentation/model.blend`
モデル、元マップ、比較画像、検証JSONはReleaseに保存済み。元添付PNGそのものは未保存で、実画像由来・同解像度のWebP参照版をmainへ保存済み（INPUTS.md）。

## 続行するとき
この文書より最新実状態を優先する。`workspace-state` の `workspaces/worn-violet-rabbit-20260918/state.json`、`jobs/refine-v003.json`、対応Actions、Release manifestを照合する。実行中なら追跡する。失敗・中断ならdocs/RESUME.mdに従い、有効snapshotから新job IDで必要な工程だけを再開する。
成功ならcreative-review/creative-host artifactを取得し、package/comparison.png、three_view.png、details.png、presentation/viewsの実画像を開く。`evidence/refine-v003/` のexact manifest/readback結果とファイルを照合し、BRIEFに対する対象版レビューを保存する。問題は新しい版で修正し、未見・未検証の内容を合格扱いしない。

## 過去の失敗
build-v001はtextures/model成功、presentationが実環境のOpenImageDenoiser非対応で失敗。診断はreviews/build-v001-diagnostic.md。有効なモデル完了snapshotからrender-v002で復旧済み。初期の明るすぎる画像や合成grid模様を最終品質と混同しない。
