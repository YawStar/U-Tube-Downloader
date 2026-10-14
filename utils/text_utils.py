# -*- coding: utf-8 -*-
"""
စာသား ပြောင်းလဲခြင်း helper များ။

Video Description ထဲက URL များကို clickable hyperlink အဖြစ်
ပြောင်းပေးသည်။ main.py ရဲ့ display_video_info() နဲ့
on_download_finished() နှစ်ခုလုံးမှာ ထပ်ခါတလဲလဲ ရေးနေရတဲ့
logic များ
"""
import re
import html as html_module

# main.py ရဲ့ url_pattern နဲ့ ကွက်တိတူ
URL_PATTERN = r'(https?://[^\s<>"]+)'

# main.py ရဲ့ inline style နဲ့ ကွက်တိတူ
LINK_STYLE = 'color: #3498db; text-decoration: underline;'

def description_to_html(text) -> str:
    """
    Video Description ကို HTML အဖြစ် ပြောင်းပြီး URL များကို
    clickable hyperlink ဖြစ်အောင်လုပ်

    YouTube/Matroska metadata မှာ newline တွေကို " / " (သို့မဟုတ်) " /  / "
    အဖြစ် သိမ်းထားတတ်တဲ့အတွက် ဒါတွေကို line/paragraph break အဖြစ်
    ပြန်ပြောင်း

    Args:
        text: မူရင်း description (str သို့မဟုတ် None)

    Returns:
        HTML string — QTextBrowser.setHtml() အတွက်
    """
    if text is None:
        text = ""

    s = str(text)

    # ─── ၁။ URL တွေကို placeholder နဲ့ protect (slash replace မထိခိုက်အောင်) ───
    url_pattern = re.compile(r"(https?://[^\s<>\"']+)")
    urls = []

    def _protect(match):
        urls.append(match.group(0))
        return f"\x00URL{len(urls) - 1}\x00"

    s = url_pattern.sub(_protect, s)

    # ─── ၂။ " /  / " (slash နှစ်ခု) → paragraph break (\n\n) ───
    #    single slash က အရင်ဖမ်းမိရင် ပြဿနာမဖြစ်အောင်လုပ်
    s = re.sub(r"\s*/\s*/\s*", "\n\n", s)

    # ─── ၃။ " / " (slash တစ်ခုတည်း) → line break (\n) ───
    #    space နှစ်ဖက်ရှိတဲ့ slash ကိုပဲ ဖမ်း (and/or, 1/2 မပျက်အောင်)
    s = re.sub(r"\s+/\s+", "\n", s)

    # ─── ၄။ Line ending အားလုံး normalize ───
    s = (
        s.replace("\r\n", "\n")
         .replace("\r", "\n")
         .replace("\u2028", "\n")
         .replace("\u2029", "\n")
         .replace("\x0b", "\n")
         .replace("\x0c", "\n")
    )

    # ─── ၅။ HTML escape ───
    escaped = html_module.escape(s)

    # ─── ၆။ URL တွေကို link အဖြစ် ပြန်ထည့် ───
    def _restore(match):
        idx = int(match.group(1))
        url = urls[idx]
        return f'<a href="{url}" style="{LINK_STYLE}">{url}</a>'

    with_links = re.sub(r"\x00URL(\d+)\x00", _restore, escaped)

    # ─── ၇။ Paragraph + line break ───
    paragraphs = with_links.split("\n\n")
    html_parts = []
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        para_html = para.replace("\n", "<br>")
        html_parts.append(f"<p style='margin: 0 0 10px 0;'>{para_html}</p>")

    return "".join(html_parts)