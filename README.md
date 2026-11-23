# ピクトレ公式サイト（pictree.greenwaygrid.global）

旧WordPressサイトを静的サイトに移したもの。Netlifyで公開（公開フォルダは `site/`）。

- `site/` 公開するファイル一式（記事・規約類・FAQ・フォーム・画像）。URLは旧サイトと同じ
- `site/_redirects` 旧サイトのページ送り・日英の振り分けの転送
- `tools/migrate/` 旧WordPressから記事を取り出して変換したプログラム（記録用）
- 規約類（/terms-of-use/ ほか）は旧サイトの本文を一字一句そのまま移している。文言を変えるときは改定の手続きを経ること
- `netlify.toml` の noindex は、本番ドメインへの切り替え時に外す
