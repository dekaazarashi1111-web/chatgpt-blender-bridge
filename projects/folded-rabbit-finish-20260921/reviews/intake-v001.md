# intake-v001 の技術確認 / 視覚レビュー未了

対象source: `065eb820df9e64af1806c5d1174e3ddd1346c61c`
対象Release: `creative-folded-rabbit-finish-20260921-intake-v001-35563023916-1-1`
対象archive SHA256: `c5d41457ff3dbf988a6ac57b5ada016c0d020821be67c33024f1b80e81942bc2`
対象manifest SHA256: `50dc6458d91ef183ff68e20110674bf9f0e04bd262c61cbf3f560d1f3f511e4a`
実行: https://github.com/dekaazarashi1111-web/chatgpt-blender-bridge/actions/runs/35563023916

## 判定
技術的な継承/保存: 合格。形状の見た目: **未レビュー**。依頼の造形仕上げ: **未完了**。
これはapprovalではない。実画像が見られないことは形状自体の不合格を示すものでもないため、視覚的changes_requestedを捏造しない。workflowへの機械判定JSONは提出せず、stateはneeds_reviewを維持する。

## このセッションで確認できた根拠
GitHub Actionsのprepare/create全step、同commitのvalidate、intake exit0、workspace-state、Release assetのsize/digestを照合した。create job106219389179の実ログには以下がある。
- 親v006の244430468-byte archiveを実ダウンロードし、manifest/archiveの両固定hashと全128ファイルを検証した。
- model.blendは159212580 bytes、SHA256 aa98019f06ff34ea3d700981ad594947dbb55ac6379bcb22a4a2ab2980d03b08。geometry_modified=false。
- 35画像エントリ（重複/参照/小画像を含む）を保持しPillow decode。新しいBlenderレンダーではない。
- 新Releaseのmanifest実バイトをCIが読み戻しhash照合、134ファイルのsize/hashとserver archive digestを検証。publication_errors=[]。
- 軽量visual artifactの作成・取得に成功。大容量.blendと画像を別々に取得できる実行経路を追加し、実運用で成功した。

## 確認していないこと
実画像をこのセッションで開いて元の3画像と見比べる作業はできていない。container/Python/open_imageのTransportTimeoutErrorが継続し、小さいZIPや別の表示経路でも解消しなかった。新Release archiveをChatGPTのローカル環境で再取得・独立照合したとも主張しない。CIのmanifest読み戻しはarchive本体の再ダウンロードとは別である。
新しい形状変更、今回のBlender再実行、最終材質/テクスチャ、完成判定は行っていない。元v006の実行成功や技術検査記録を見た目の完成と同一視しない。

## 次のレビュー対象
本保存地点の実head_front/right/three_quarter/uniform_clayを見て、口元の凸曲面、鼻梁、頬の統合と接合溝、眼窩の滑らかさを確認する。全身/折れ耳/手足の13ビューを参照と比較する。見えていない差異の大小や完全再現率は記入しない。必要な修正があれば新job IDを使い、対象版の実画像をレビューした後に保存済みsource/archiveを固定した判定を記録する。
