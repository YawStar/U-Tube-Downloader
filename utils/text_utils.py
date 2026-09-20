# -*- coding: utf-8 -*-
"""
စာသား ပြောင်းလဲခြင်း helper များ။

Video Description ထဲက URL များကို clickable hyperlink အဖြစ်
ပြောင်းပေးသည်။ main.py ရဲ့ display_video_info() နဲ့
on_download_finished() နှစ်ခုလုံးမှာ ထပ်ခါတလဲလဲ ရေးနေရတဲ့
logic ကို စုစည်းထားသည်။
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
    clickable hyperlink ဖြစ်စေသည်။

    main.py ရဲ့ ဒီ block ကို တိတိကျကျ အစားထိုးသည်:

        url_pattern = r'(https?://[^\\s<>"]+)'
        import html
        escaped_desc_text = html.escape(str(desc_text))
        html_text = re.sub(url_pattern,
                           r'<a href="\\1" style="color: #3498db; text-decoration: underline;">\\1</a>',
                           escaped_desc_text)
        html_text = html_text.replace("\\n", "<br>")
        self.txtInfoLog.setHtml(html_text)

    Args:
        text: မူရင်း description (str သို့မဟုတ် None)

    Returns:
        HTML string — QTextBrowser.setHtml() အတွက် အဆင်သင့်
    """
    if text is None:
        text = ""

    # HTML special chars escape (&, <, >, ", ')
    # ⚠️ main.py က html.escape() ကို quote=True default အတိုင်း ခေါ်သည်
    escaped = html_module.escape(str(text))

    # URL → <a href="...">...</a>
    with_links = re.sub(
        URL_PATTERN,
        rf'<a href="\1" style="{LINK_STYLE}">\1</a>',
        escaped,
    )

    # Newline → <br>
    return with_links.replace("\n", "<br>")