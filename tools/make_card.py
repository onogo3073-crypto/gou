"""SNS用の「会長の言葉」カード画像（1080×1350、Instagram 4:5）を作ります。

使い方:
  python3 tools/make_card.py 出力.png "見出し" "本文（改行は \\n）" ["シリーズ名"]
例:
  python3 tools/make_card.py sns/cards/w1.png "勝利にこだわる。\\nただし、無理はさせない。" "勝つために子どもを使い捨てにすることは、断じてしない。" "会長の言葉 #01"
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 1080, 1350
NAVY, GOLD, WHITE, SUB, RED = (33, 30, 57), (216, 168, 58), (255, 255, 255), (159, 176, 204), (213, 33, 42)
FONT_PATHS = [
    "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf",
    "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
]


def load_font(size):
    for p in FONT_PATHS:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.truetype("IPAGothic", size)


def wrap(draw, text, font, width):
    lines = []
    for para in text.split("\n"):
        line = ""
        for ch in para:
            if draw.textlength(line + ch, font=font) > width and line:
                lines.append(line)
                line = ch
            else:
                line += ch
        lines.append(line)
    return lines


def make(out, title, body, series="会長の言葉"):
    img = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(img)
    d.rectangle([60, 60, W - 60, H - 60], outline=GOLD, width=3)

    logo = os.path.join(ROOT, "business", "assets", "logo.png")
    if os.path.exists(logo):
        lg = Image.open(logo).convert("RGBA")
        lg.thumbnail((110, 130))
        img.paste(lg, ((W - lg.width) // 2, 110), lg)

    f_series, f_title, f_body, f_foot = load_font(34), load_font(68), load_font(40), load_font(30)
    d.text((W // 2, 290), series, font=f_series, fill=GOLD, anchor="mm")
    d.line([W // 2 - 60, 330, W // 2 + 60, 330], fill=GOLD, width=2)

    y = 420
    for line in wrap(d, title, f_title, W - 220):
        d.text((W // 2, y), line, font=f_title, fill=WHITE, anchor="mm")
        y += 92
    y += 40
    for line in wrap(d, body, f_body, W - 260):
        d.text((W // 2, y), line, font=f_body, fill=(220, 226, 238), anchor="mm")
        y += 64

    d.text((W // 2, H - 200), "狭山西武ボーイズ 会長　小野 剛", font=f_foot, fill=WHITE, anchor="mm")
    d.text((W // 2, H - 150), "元プロ野球選手（読売ジャイアンツ）", font=load_font(24), fill=SUB, anchor="mm")
    d.rectangle([60, H - 100, W - 60, H - 60], fill=RED)
    d.text((W // 2, H - 80), "野球で人物を磨き、人物の集まりが強いチームを生む", font=load_font(24), fill=WHITE, anchor="mm")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    img.save(out, "PNG")
    print("作成しました:", out)


if __name__ == "__main__":
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    make(sys.argv[1], sys.argv[2].replace("\\n", "\n"), sys.argv[3].replace("\\n", "\n"), *(sys.argv[4:5] or []))
