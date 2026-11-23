"""Build list pages (/news/, /season/, /event/ and /en/ versions) from index.json, plus Netlify _redirects."""
import json, os, re, sys, html
sys.path.insert(0, "/tmp/gen")
import gen

items = json.load(open("/tmp/gen/index.json", encoding="utf-8"))
T = open("/tmp/gen/article.html", encoding="utf-8").read()
T = re.sub(r'\s*<div class="meta">.*?</div>', "", T, flags=re.S)
T = T.replace('<a class="back" href="{{list_url}}">← {{back}}</a>', "")
T = T.replace('<a href="{{list_url}}">{{type_label}}</a>', "{{type_label}}")
CSS = """
.list{list-style:none;margin:0;padding:0}
.list li{border-bottom:1px solid var(--line)}
.list a{display:flex;gap:16px;padding:14px 4px;text-decoration:none;color:var(--ink)}
.list a:hover .t{color:var(--blue2)}
.list time{flex:0 0 7.5em;color:var(--ink3);font-size:14px}
.list .t{font-weight:500}
.tabs{display:flex;gap:8px;margin:0 0 20px;flex-wrap:wrap}
.tabs a{border:2px solid var(--navy);border-radius:999px;padding:3px 16px;text-decoration:none;color:var(--navy);font-weight:700;font-size:14px}
.tabs a.on{background:var(--navy);color:#fff}
@media (max-width:720px){.list a{flex-direction:column;gap:2px}}
"""
T = T.replace("@media (max-width:720px)", CSS + "@media (max-width:720px)")
NAMES = {"ja": {"news": "ニュース", "season": "シーズン", "event": "イベント"},
         "en": {"news": "News", "season": "Seasons", "event": "Events"}}

def tabs(lang, cur):
    pre = "/en" if lang == "en" else ""
    return '<div class="tabs">' + "".join(
        f'<a class="{"on" if t == cur else ""}" href="{pre}/{t}/">{NAMES[lang][t]}</a>' for t in ["news", "season", "event"]) + "</div>"

redirects = []
for lang in ["ja", "en"]:
    for t in ["news", "season", "event"]:
        rows = sorted([i for i in items if i["lang"] == lang and i["type"] == t], key=lambda i: (i["date"], i["id"]), reverse=True)
        lis = "".join(f'<li><a href="{i["path"]}"><time datetime="{i["date"]}">{i["date"].replace("-", ".")}</time><span class="t">{html.escape(i["title"])}</span></a></li>' for i in rows)
        path = ("/en" if lang == "en" else "") + f"/{t}/"
        title = NAMES[lang][t]
        page = (T.replace("{{lang}}", lang).replace("{{title}}", title).replace("{{desc}}", title + "｜ピクトレ")
                .replace("{{canonical}}", gen.SITE + path).replace("{{og_image}}", gen.SITE + "/assets/logo.png")
                .replace("{{type_label}}", title).replace("{{hero}}", "").replace("{{body}}", tabs(lang, t) + f'<ul class="list">{lis}</ul>')
                .replace("{{home}}", "/en/" if lang == "en" else "/").replace("{{nav}}", gen.NAV[lang])
                .replace("{{footer_links}}", "".join(f'<li><a href="{u}">{x}</a></li>' for u, x in gen.footer_links(lang))))
        os.makedirs(gen.OUT + path, exist_ok=True)
        open(gen.OUT + path + "index.html", "w", encoding="utf-8").write(page)
        redirects.append(f"{path}page/*  {path}  301")
        print(path, len(rows))

open(gen.OUT + "/_redirects", "w").write("\n".join(redirects) + "\n")
