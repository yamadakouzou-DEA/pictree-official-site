"""Convert WordPress posts (news/season/event) from the public REST API into static pages.
Usage: python3 -I gen.py <type> <id> [<id> ...]   (type: news|season|event; lang auto from link)
"""
import json, os, re, sys, html, urllib.request, urllib.parse

SITE = "https://pictree.greenwaygrid.global"
OUT = "/home/claude/pictree-site"
UA = {"User-Agent": "Mozilla/5.0 (pictree-migration)"}

def get(url, binary=False):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
    return data if binary else data.decode("utf-8")

def download_upload(abs_url):
    """Mirror /wp-content/uploads/... to the same path in the site. Returns root-relative path."""
    path = urllib.parse.urlparse(abs_url).path
    if not path.startswith("/wp-content/uploads/"):
        return abs_url
    dest = OUT + urllib.parse.unquote(path)
    if not os.path.exists(dest):
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        try:
            with open(dest, "wb") as f:
                f.write(get(abs_url, binary=True))
        except Exception as e:
            print("  image failed:", abs_url, e)
    return path

def clean(content):
    content = re.sub(r'\s(srcset|sizes)="[^"]*"', "", content)
    content = re.sub(r'<div style="height:\d+px" aria-hidden="true" class="wp-block-spacer"></div>', '<div class="sp"></div>', content)
    def img(m):
        return m.group(1) + download_upload(m.group(2)) + m.group(3)
    content = re.sub(r'(<img[^>]*?\ssrc=")(https?://pictree\.greenwaygrid\.global/wp-content/uploads/[^"]+)(")', img, content)
    # links to uploads (PDF etc.)
    content = re.sub(r'(href=")(https?://pictree\.greenwaygrid\.global/wp-content/uploads/[^"]+)(")', img, content)
    # internal links -> root-relative
    content = re.sub(r'((?:href|src)=["\'])https?://pictree\.greenwaygrid\.global/', r'\1/', content)
    content = re.sub(r'<iframe[^>]*class="wp-embedded-content"[^>]*>\s*</iframe>', '', content)
    content = content.replace('href="/wp-admin/edit.php?post_type=news"', 'href="/en/news/"')
    content = re.sub(r'href="([^"]*?)\s+"', r'href="\1"', content)
    content = re.sub(r"\n{3,}", "\n", content)
    return content

def og_image(link):
    try:
        page = get(link)
        m = re.search(r'<meta property="og:image" content="([^"]+)"', page)
        return m.group(1) if m else None
    except Exception:
        return None

LABEL = {"ja": {"news": "ニュース", "season": "シーズン", "event": "イベント", "home": "トップ",
                "back": "ニュース一覧へ戻る", "terms": "利用規約", "policy": "プライバシーポリシー",
                "psa": "資金決済法に基づく表示", "tokusho": "特定商取引法に基づく表示", "form": "お問い合わせ", "faq": "よくある質問"},
         "en": {"news": "News", "season": "Season", "event": "Event", "home": "Home",
                "back": "Back to news", "terms": "Terms of Use", "policy": "Privacy Policy",
                "psa": "", "tokusho": "", "form": "Contact", "faq": "FAQ"}}

def footer_links(lang):
    if lang == "en":
        return [("/en/terms-of-use-en/", "Terms of Use"), ("/en/policy-en/", "Privacy Policy"), ("/en/faq-en/", "FAQ"), ("/en/form-en/", "Contact")]
    return [("/terms-of-use/", "利用規約"), ("/policy/", "プライバシーポリシー"), ("/payment-services-act/", "資金決済法に基づく表示"),
            ("/terms/", "特定商取引法に基づく表示"), ("/faq/", "よくある質問"), ("/form/", "お問い合わせ")]

NAV = {"ja": '<li><a href="/">トップ</a></li><li><a href="/news/">ニュース</a></li><li><a href="/business/">法人・自治体の方へ</a></li>',
       "en": '<li><a href="/en/">Home</a></li><li><a href="/en/news/">News</a></li>'}

TEMPLATE = open(os.path.join(os.path.dirname(__file__), "article.html"), encoding="utf-8").read()

def build(ptype, pid):
    p = json.loads(get(f"{SITE}/wp-json/wp/v2/{ptype}/{pid}"))
    link = p["link"]
    path = urllib.parse.urlparse(link).path.rstrip("/")
    lang = "en" if path.startswith("/en/") else "ja"
    L = LABEL[lang]
    title = html.unescape(re.sub("<[^>]+>", "", p["title"]["rendered"]))
    date = p["date"][:10]
    y, m, d = date.split("-")
    date_disp = f"{y}年{int(m)}月{int(d)}日" if lang == "ja" else f"{y}-{m}-{d}"
    hero = og_image(link)
    hero_html = ""
    if hero and "/wp-content/uploads/" in hero:
        hero_html = f'<img class="hero" src="{download_upload(hero)}" alt="">'
    body = clean(p["content"]["rendered"])
    desc = html.unescape(re.sub(r"\s+", " ", re.sub("<[^>]+>", "", p["content"]["rendered"]))).strip()[:110]
    list_url = "/en/news/" if lang == "en" else "/news/"
    page = (TEMPLATE
            .replace("{{lang}}", lang)
            .replace("{{title}}", html.escape(title))
            .replace("{{desc}}", html.escape(desc))
            .replace("{{canonical}}", SITE + path + "/")
            .replace("{{og_image}}", (SITE + download_upload(hero)) if hero_html else SITE + "/assets/logo.png")
            .replace("{{type_label}}", L[ptype])
            .replace("{{date_iso}}", date)
            .replace("{{date}}", date_disp)
            .replace("{{hero}}", hero_html)
            .replace("{{body}}", body)
            .replace("{{list_url}}", list_url)
            .replace("{{back}}", L["back"])
            .replace("{{home}}", "/en/" if lang == "en" else "/")
            .replace("{{nav}}", NAV[lang])
            .replace("{{footer_links}}", "".join(f'<li><a href="{u}">{t}</a></li>' for u, t in footer_links(lang))))
    out = OUT + path + "/index.html"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8").write(page)
    meta = {"id": pid, "type": ptype, "lang": lang, "path": path + "/", "title": title, "date": date}
    print(json.dumps(meta, ensure_ascii=False))
    return meta

if __name__ == "__main__":
    for i in sys.argv[2:]:
        build(sys.argv[1], int(i))
