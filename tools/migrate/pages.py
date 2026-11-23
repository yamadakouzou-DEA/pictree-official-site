"""Migrate fixed pages (terms, policy, legal notices, FAQ, contact form) from saved HTML to static pages."""
import os, re, sys
from bs4 import BeautifulSoup
sys.path.insert(0, "/tmp/gen")
import gen

SRC = "/tmp/cur/pages"
OUT = gen.OUT
T = open("/tmp/gen/article.html", encoding="utf-8").read()
T = re.sub(r'\s*<div class="meta">.*?</div>', "", T, flags=re.S)
T = T.replace('<a class="back" href="{{list_url}}">← {{back}}</a>', "")
T = T.replace('<a href="{{list_url}}">{{type_label}}</a>', "{{type_label}}")
EXTRA_CSS = """
.body h3{font-size:17px;margin:2em 0 .6em;padding-left:10px;border-left:4px solid var(--yellow)}
.p-faq__ctg{font-family:var(--fd);font-weight:900;color:var(--navy);font-size:20px;margin:36px 0 12px}
.p-faq__list{list-style:none;padding:0;margin:0}
.p-faq__list__item{list-style:none;border:1px solid var(--line);border-radius:12px;padding:14px 18px;margin:0 0 10px;background:#fff}
.p-faq__list__item__title{font-weight:700;color:var(--navy)}
.p-faq__list__item__title::before{content:"Q. ";color:var(--blue2)}
.p-faq__list__item__cap{margin:8px 0 0;color:var(--ink2)}
.form dl{margin:0 0 18px}.form dd{margin:0}
.body li:empty{display:none}.body ul{padding-left:1.2em}.body li{margin:0 0 12px}.form dt{font-weight:700;margin-bottom:6px}.form dt span{color:#B4432F;font-size:12px;margin-left:8px}
.form input[type=text],.form input[type=email],.form textarea{width:100%;font:inherit;padding:10px 12px;border:1.5px solid var(--line);border-radius:10px}
.form button{font:inherit;font-weight:700;background:var(--blue2);color:#fff;border:2px solid var(--navy);border-radius:999px;padding:10px 32px;box-shadow:0 3px 0 var(--navy);cursor:pointer}
.form .hp{display:none}
"""
T = T.replace("@media (max-width:720px)", EXTRA_CSS + "@media (max-width:720px)")

PAGES = [  # (source file, url path, lang, title)
    ("terms-of-use.html", "/terms-of-use/", "ja", "利用規約"),
    ("policy.html", "/policy/", "ja", "プライバシーポリシー"),
    ("payment-services-act.html", "/payment-services-act/", "ja", "資金決済法に基づく表示"),
    ("terms.html", "/terms/", "ja", "特定商取引法に基づく表示"),
    ("faq.html", "/faq/", "ja", "よくある質問"),
    ("en_terms-of-use-en.html", "/en/terms-of-use-en/", "en", "Terms of Use"),
    ("en_policy-en.html", "/en/policy-en/", "en", "Privacy Policy"),
    ("en_faq-en.html", "/en/faq-en/", "en", "FAQ"),
]

def body_of(fname):
    s = BeautifulSoup(open(os.path.join(SRC, fname), encoding="utf-8"), "html.parser")
    u = s.select_one("div.l-upage")
    block = [c for c in u.find_all(recursive=False) if "l-upage__header" not in (c.get("class") or [])][0]
    inner = block.find("div") or block
    html_ = inner.decode_contents()
    return gen.clean(html_)

def render(path, lang, title, body):
    page = (T.replace("{{lang}}", lang).replace("{{title}}", title).replace("{{desc}}", title + "｜ピクトレ")
            .replace("{{canonical}}", gen.SITE + path).replace("{{og_image}}", gen.SITE + "/assets/logo.png")
            .replace("{{type_label}}", title).replace("{{hero}}", "").replace("{{body}}", body)
            .replace("{{home}}", "/en/" if lang == "en" else "/").replace("{{nav}}", gen.NAV[lang])
            .replace("{{footer_links}}", "".join(f'<li><a href="{u}">{t}</a></li>' for u, t in gen.footer_links(lang))))
    out = OUT + path + "index.html"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8").write(page)
    print("wrote", path)

FORM_JA = """
<p>ピクトレに関するお問い合わせは、以下のフォームからお送りください。</p>
<form class="form" name="contact-ja" method="POST" action="/form/thanks/" data-netlify="true" netlify-honeypot="bot-field">
<input type="hidden" name="form-name" value="contact-ja">
<p class="hp"><label>入力しないでください <input name="bot-field"></label></p>
<dl><dt>お名前<span>※必須</span></dt><dd><input type="text" name="name" autocomplete="name" required maxlength="400"></dd></dl>
<dl><dt>メールアドレス<span>※必須</span></dt><dd><input type="email" name="email" autocomplete="email" required maxlength="400"></dd></dl>
<dl><dt>お問い合わせ内容<span>※必須</span></dt><dd><textarea name="message" rows="10" required maxlength="2000"></textarea></dd></dl>
<p><a href="/policy/" target="_blank">プライバシーポリシー</a>に同意の上、送信ボタンを押してください。</p>
<p><button type="submit">送信する</button></p>
</form>"""
FORM_EN = """
<p>Please use the form below to contact us about PicTrée.</p>
<form class="form" name="contact-en" method="POST" action="/en/form-en/thanks/" data-netlify="true" netlify-honeypot="bot-field">
<input type="hidden" name="form-name" value="contact-en">
<p class="hp"><label>Do not fill this out <input name="bot-field"></label></p>
<dl><dt>Name<span>Required</span></dt><dd><input type="text" name="name" autocomplete="name" required maxlength="400"></dd></dl>
<dl><dt>Email<span>Required</span></dt><dd><input type="email" name="email" autocomplete="email" required maxlength="400"></dd></dl>
<dl><dt>Message<span>Required</span></dt><dd><textarea name="message" rows="10" required maxlength="2000"></textarea></dd></dl>
<p>Please agree to our <a href="/en/policy-en/" target="_blank">Privacy Policy</a> before submitting.</p>
<p><button type="submit">Send</button></p>
</form>"""

if __name__ == "__main__":
    for f, path, lang, title in PAGES:
        render(path, lang, title, body_of(f))
    render("/form/", "ja", "お問い合わせ", FORM_JA)
    render("/en/form-en/", "en", "Contact", FORM_EN)
    render("/form/thanks/", "ja", "送信が完了しました", "<p>お問い合わせを受け付けました。内容を確認のうえ、担当者よりご連絡いたします。</p><p><a href=\"/\">トップへ戻る</a></p>")
    render("/en/form-en/thanks/", "en", "Thank you", "<p>We have received your message and will get back to you.</p><p><a href=\"/en/\">Back to home</a></p>")
