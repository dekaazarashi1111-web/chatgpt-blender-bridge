# 進捗と再開入口

## 現在
`render-v002` 実行中。最新確認でcarry工程が成功し、保存済みモデルから比較レンダー中。重複投入しない。
- Source: `437b1cdceb06e5129ee51b858581db1f2cc6dfcc`
- Actions: https://github.com/dekaazarashi1111-web/chatgpt-blender-bridge/actions/runs/35365556050
- Runtime: `ghcr.io/dekaazarashi1111-web/chatgpt-creative-runtime@sha256:994a4dee98e41654e64d799d830210edd763b8be323d8dfc9f5709d0e6dd7327`
- Started: `2026-09-18T15:58:03.638369Z`
このruntime digestはbuild-v001と異なる。各実行の実測reportを優先する。

## 完了／失敗
`build-v001` は textures と model 成功。実 .blend 再読込pass、外部依存欠落0、155 renderable objects、149845頂点、全高約2.599m。これらの技術検査と実ファイルを確認した。
presentationは実環境のOpenImageDenoiser非対応で失敗、package未実行。実際の512px front/right/back/three_quarterを開いたが、明るさ、目の突出、損傷の四角さ、耳の板状感に差があり、外観合格とはしない。
詳しくは `reviews/build-v001-diagnostic.md`。render-v002はノイズ除去無効・128samplesとし、造形とマップを作り直さずモデル完了snapshotを復元した。

## 有効なモデル保存地点
Release: https://github.com/dekaazarashi1111-web/chatgpt-blender-bridge/releases/tag/creative-worn-violet-rabbit-20260918-build-v001-35364229702-1-2
- archive_sha256: `ef849df8211ccb60e4fc64a3899384720f1e31d428575e432d8b1a4e2da30ef8`
- manifest_sha256: `a05be2b321e5345acac7f6905dce8fb63d4a33d702c92139ec580ac6da929dc1`
- source blend: `output/model/model.blend`
本体と2KテクスチャがGitHub Releaseに保存済み。元添付PNGは未保存で、実画像由来のフル解像度WebP参照版をmainへ保存済み（INPUTS.md参照）。

## 継続の必須確認
この文書より最新実状態を優先する。
`workspace-state` の `workspaces/worn-violet-rabbit-20260918/state.json` と `jobs/render-v002.json`、対応Actions、Release manifestを照合する。
実行中なら追跡。失敗・中断ならdocs/RESUME.mdに従い別job IDで復元。完了ならActionsのcreative-review artifactをダウンロードし、package/comparison.png, three_view.png, details.png, presentation/viewsを開いて比較する。
`evidence/render-v002/` にreadback.jsonとReleaseから再取得した正確なmanifestが保存される予定。まだ監査成功と主張しない。

## 次の作業
水平・同縮尺・中性照明の実画像で参考との違いを確認し、目／顔のつながり、耳の厚み、不規則な損傷、紫の明度・模様を必要に応じて部分修正する。対象版のレビューをpinして保存し、最終成果物を案内する。現状は完成・外観承認ではない。
