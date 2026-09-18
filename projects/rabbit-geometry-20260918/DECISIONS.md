# 決定事項と実行環境

- 起点はリモートmain `a55cb73d8a6f4f5c8b6c03a308efd86b3ab7b179`。そのcommitの開始プロンプト、README、EXECUTION_CONTRACT、tools、schema、v2サンプル、INPUTS、RESUME、tool_entry、preview実装、creative-job workflowを確認した。root AGENTS.mdは404、projects直下の一覧にAGENTS.mdはない。新規作品内に上位指示ファイルはない。
- shell `git ls-remote https://github.com/dekaazarashi1111-web/chatgpt-blender-bridge.git refs/heads/main` は `Could not resolve host: github.com` で失敗。GitHub接続のreadとGit Data APIを使う。archive downloadも取得に至らず。これをGitHub接続の権限不足とは扱わない。
- 新規stateの読み取りは404。開始時点のin_progress Actionsは0件。旧作品の途中版を今回の完成品にしない。
- 利用ツールは登録済みBlender/Python。既存runtimeを利用し、実際の版とimage digestは実行記録を正とする。標準制作予算18000秒、最大19800秒を守る。最初は短い造形工程と検証画像工程へ分割。
- dispatch専用操作は現在の接続に見当たらない。確認したworkflowのmainへのjob.json追加pushトリガーを利用し、実際のActions発生を確認する。
- 今回は単色の部位材質のみ。テクスチャ生成、画像投影による見かけの補正、既存材質の移植はしない。
- 参照で見えない頭内部は簡潔な暗い空洞、関節内部は控えめな円筒とする。元のエンドスケルトンを復元したとは呼ばない。
- 正面で向かって左の上腕・前側大腿に欠損。背面画像の欠損位置は正面と鏡映的に整合しないため、背面で向かって左に見える反対脚の後面にも別の浅い欠損を設ける。これは三方向を矛盾なく満たすための補完。
