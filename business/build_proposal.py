"""協賛提案書（2027年度）を Word で生成します。

使い方: python3 business/build_proposal.py
出力:
  output/協賛提案書_2027年度.docx      … 振込先入り（business/private/振込先.md がある場合）
  business/協賛提案書_2027年度_見本.docx … 振込先を伏せた見本（公開リポジトリ用）

数値の根拠は business/sns_実績_2026-11-04.md と team_profile.md です。
"""
import os
import re

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Mm, Pt, RGBColor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT = "ＭＳ ゴシック"
NAVY, GOLD, RED, PAPER, GRAY = "211E39", "B8862B", "C8202A", "F2F0EA", "5A6274"

# ---------- 書式の部品 ----------

def font(run, size=10, bold=False, color=None):
    run.font.name = FONT
    run.font.size = Pt(size)
    run.font.bold = bold
    run._element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:eastAsia"), FONT)
    if color:
        run.font.color.rgb = RGBColor.from_string(color)
    return run


def para(container, text="", size=10, bold=False, color=None, align=None, before=0, after=3):
    p = container.add_paragraph()
    f = p.paragraph_format
    f.space_before, f.space_after = Pt(before), Pt(after)
    f.line_spacing_rule = WD_LINE_SPACING.SINGLE
    if align:
        p.alignment = align
    for i, part in enumerate(re.split(r"\*\*", text)):
        if part:
            font(p.add_run(part), size, bold or i % 2 == 1, color)
    return p


def shade(cell, fill):
    pr = cell._element.get_or_add_tcPr()
    sh = OxmlElement("w:shd")
    sh.set(qn("w:val"), "clear")
    sh.set(qn("w:color"), "auto")
    sh.set(qn("w:fill"), fill)
    pr.append(sh)


def fix_widths(table, widths):
    table.autofit = False
    for i, w in enumerate(widths):
        table.columns[i].width = Mm(w)
        for cell in table.columns[i].cells:
            cell.width = Mm(w)


def borders(table, color="D8D4C8", size=4):
    tbl_pr = table._element.tblPr
    b = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        e = OxmlElement(f"w:{edge}")
        e.set(qn("w:val"), "single" if size else "nil")
        e.set(qn("w:sz"), str(size))
        e.set(qn("w:color"), color)
        b.append(e)
    tbl_pr.append(b)


def cell_text(cell, text, size=10, bold=False, color=None, align=WD_ALIGN_PARAGRAPH.LEFT, fill=None):
    cell.text = ""
    lines = text.split("\n")
    p = cell.paragraphs[0]
    for i, line in enumerate(lines):
        if i:
            p = cell.add_paragraph()
        p.alignment = align
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
        for j, part in enumerate(re.split(r"\*\*", line)):
            if part:
                font(p.add_run(part), size, bold or j % 2 == 1, color)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    if fill:
        shade(cell, fill)


NUM = re.compile(r"^[\d,]+(円|名|回|人|件|社|%|％)?$|^約[\d,.]+")
YEAR = re.compile(r"^\d{4}年(\d{1,2}月)?$|^\d{4}年\d{1,2}月〜")


def table(doc, rows, widths, head=True, size=9.5, center_cols=()):
    t = doc.add_table(rows=len(rows), cols=len(rows[0]))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    borders(t)
    for r, row in enumerate(rows):
        for c, text in enumerate(row):
            cell = t.cell(r, c)
            cell.width = Mm(widths[c])
            if r == 0 and head:
                cell_text(cell, text, size, True, "FFFFFF", WD_ALIGN_PARAGRAPH.CENTER, NAVY)
                continue
            align = WD_ALIGN_PARAGRAPH.LEFT
            if c in center_cols or YEAR.match(text) or text in ("○", "－", "◎"):
                align = WD_ALIGN_PARAGRAPH.CENTER
            elif NUM.match(text):
                align = WD_ALIGN_PARAGRAPH.RIGHT
            cell_text(cell, text, size, c == 0 and not YEAR.match(text), None, align, PAPER if r % 2 == 0 else None)
    fix_widths(t, widths)
    para(doc, "", after=2)
    return t


def heading(doc, no, title, lead=None):
    t = doc.add_table(rows=1, cols=2)
    borders(t, size=0)
    a, b = t.cell(0, 0), t.cell(0, 1)
    fix_widths(t, [14, 156])
    cell_text(a, no, 14, True, "FFFFFF", WD_ALIGN_PARAGRAPH.CENTER, NAVY)
    cell_text(b, title, 13, True, NAVY, fill="E9E6DC")
    para(doc, "", after=1)
    if lead:
        para(doc, lead, 10.5, True, NAVY, after=5)


def kpi_boxes(doc, items):
    t = doc.add_table(rows=2, cols=len(items))
    borders(t, "FFFFFF", 12)
    for i, (num, label) in enumerate(items):
        cell_text(t.cell(0, i), num, 18, True, GOLD, WD_ALIGN_PARAGRAPH.CENTER, NAVY)
        cell_text(t.cell(1, i), label, 8.5, False, "FFFFFF", WD_ALIGN_PARAGRAPH.CENTER, NAVY)
    fix_widths(t, [170 / len(items)] * len(items))
    para(doc, "", after=2)


def note(doc, text):
    para(doc, text, 8, color=GRAY, after=4)


def page_break(doc):
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def page_number(section):
    p = section.footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    font(p.add_run("狭山西武ボーイズ　2027年度 協賛のご提案　｜　"), 8, color=GRAY)
    run = font(p.add_run(), 8, color=GRAY)
    for tag, val in (("begin", None), (None, "PAGE"), ("end", None)):
        if tag:
            el = OxmlElement("w:fldChar")
            el.set(qn("w:fldCharType"), tag)
        else:
            el = OxmlElement("w:instrText")
            el.set(qn("xml:space"), "preserve")
            el.text = val
        run._element.append(el)


def bank_text():
    path = os.path.join(ROOT, "business", "private", "振込先.md")
    if not os.path.exists(path):
        return None
    rows = dict(re.findall(r"^\| (\S+) \| (.+?) \|$", open(path, encoding="utf-8").read(), re.M))
    return f"{rows['金融機関']}　{rows['支店']}　{rows['種別']} {rows['口座番号']}　名義 {rows['名義']}"


# ---------- 本文 ----------

def build(path, bank):
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Mm(210), Mm(297)
    sec.top_margin = sec.bottom_margin = Mm(18)
    sec.left_margin = sec.right_margin = Mm(20)
    st = doc.styles["Normal"]
    st.font.name, st.font.size = FONT, Pt(10)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)

    # 表紙
    para(doc, "", after=40)
    logo = os.path.join(ROOT, "business", "assets", "logo.png")
    if os.path.exists(logo):
        p = para(doc, align=WD_ALIGN_PARAGRAPH.CENTER, after=14)
        p.add_run().add_picture(logo, width=Mm(30))
    para(doc, "SAYAMA SEIBU BOYS × HIGASHIYAMATO SAYAMA BOYS", 9, color=GRAY, align=WD_ALIGN_PARAGRAPH.CENTER, after=10)
    para(doc, "2027年度 オフィシャルパートナー", 24, True, NAVY, WD_ALIGN_PARAGRAPH.CENTER, after=2)
    para(doc, "協賛のご提案", 24, True, NAVY, WD_ALIGN_PARAGRAPH.CENTER, after=18)
    para(doc, "元プロ野球の指導陣が率いる130名の中学硬式クラブとともに、", 12, True, RED, WD_ALIGN_PARAGRAPH.CENTER, after=0)
    para(doc, "地元の子どもたちの「次の一歩」を支えていただけませんか。", 12, True, RED, WD_ALIGN_PARAGRAPH.CENTER, after=60)
    para(doc, "【　　　　　　　　　　　】御中", 14, True, NAVY, WD_ALIGN_PARAGRAPH.CENTER, after=40)
    para(doc, "2026年11月", 10, align=WD_ALIGN_PARAGRAPH.CENTER, after=2)
    para(doc, "狭山西武ボーイズ／東大和狭山ボーイズ（日本少年野球連盟）", 10, align=WD_ALIGN_PARAGRAPH.CENTER, after=2)
    para(doc, "会長　小野　剛", 11, True, align=WD_ALIGN_PARAGRAPH.CENTER)

    new = doc.add_section(WD_SECTION.NEW_PAGE)
    page_number(new)

    # 1. ご提案の要点
    heading(doc, "1", "ご提案の要点",
            "年額20万円から、狭山・東大和の子育て世帯と、数万人の野球ファンに御社名を届けます。")
    kpi_boxes(doc, [("130名", "部員数\n（二チーム制）"), ("約69万回", "SNSの表示回数\n（直近3か月）"),
                    ("6.3万回", "ドラフト指名投稿\n1本の表示回数"), ("年300日超", "活動日数の目安\n（平日夜＋土日祝）")])
    table(doc, [
        ["選んでいただく理由", "中身"],
        ["① 話題の中心にいるチーム", "2026年10月、OBの吉田健吾選手がオリックス・バファローズから育成3位指名を受けました（チーム初のプロ野球選手）。今夏の甲子園では花咲徳栄高校のスタメンにOB4名が並び、侍ジャパンU15代表にも2名が選ばれています。"],
        ["② 届く相手がはっきりしている", "部員130名の家庭（埼玉県狭山市・東京都東大和市周辺）と、Instagram・Facebook計約4,700フォロワー。発信は直近3か月で約69万回表示されました。"],
        ["③ ほかでは得られない特典", "元読売巨人軍の指導陣3名（会長・両監督）による、御社の社員ご家族向け野球教室。地域の子どもを応援する会社として、採用や社内の一体感づくりにもお使いいただけます。"],
    ], [48, 122])
    para(doc, "**お願いしたいこと：** 2027年度（2027年4月〜2028年3月）の協賛を、下記プランからご検討ください。お申込みは2027年1月末までにいただけますと、4月の新ユニフォームから御社ロゴを掲出できます。", after=6)
    note(doc, "数値の出典：部員数・会費は当チーム調べ（2026年11月4日時点）。SNSの数値はMetricoolの集計（2026年8月5日〜11月4日、Instagram・Facebook合計）。活動日数は平日練習（月〜金）と土日祝の活動からの目安です。")

    # 2. チーム紹介
    heading(doc, "2", "チーム紹介", "「全員に、試合を。」― 二つのチームで、全員に公式戦の舞台を用意しています。")
    table(doc, [
        ["項目", "内容"],
        ["チーム", "狭山西武ボーイズ（埼玉）／東大和狭山ボーイズ（東京西支部）の二チーム制"],
        ["所属", "公益財団法人 日本少年野球連盟（ボーイズリーグ）"],
        ["部員", "130名（中学1〜3年生、2026年11月時点）"],
        ["指導陣", "会長 小野剛（元読売ジャイアンツ・読売巨人軍OBスカウト）\n監督 福井敬治（元読売巨人軍）／監督 十川雄二（元読売巨人軍）"],
        ["活動", "平日 月〜金 19:00〜22:00（狭山市南入曽の専用施設）、土日祝は学年別に練習・試合"],
        ["育成方針", "勝利にこだわり、無理はさせない。「努力・思考・分析・研究・準備・駆け引き・信頼」の七つの力を、社会で通用する力として鍛えます。"],
    ], [30, 140])
    table(doc, [
        ["年", "主な実績", "出典"],
        ["2016年", "春季全国大会 準優勝", "一球速報.com"],
        ["2017年", "春季全国大会 ベスト4", "一球速報.com"],
        ["2019年", "ボーイズ選手権 ベスト8", "一球速報.com"],
        ["2026年", "東大和狭山ボーイズ 夏の選手権予選 決勝進出（決勝は読売ジャイアンツU15と対戦）", "チーム公式サイト"],
        ["2026年8月", "東大和狭山ボーイズ 関東大会 優勝（3年生最後の大会）", "チーム公式Instagram"],
        ["2026年8月", "夏の甲子園 花咲徳栄高校のスタメンにOB4名", "チーム公式Instagram"],
        ["2026年", "侍ジャパンU15代表に2名選出", "チーム公式Instagram"],
        ["2026年10月", "名古屋・四日市遠征 全国の強豪と6試合 5勝1分", "当チーム記録"],
        ["2026年10月", "OB吉田健吾選手 オリックス・バファローズ育成3位指名（チーム初のプロ野球選手）", "ベースボールキング・球歴.com"],
        ["2026年10月", "フォースキフト杯 レギュラー・ジュニア 兄弟優勝", "当チーム記録"],
        ["2026年11月", "2027年春季全国大会予選 初戦突破", "当チーム記録"],
    ], [27, 105, 38])

    page_break(doc)
    # 3. 届く相手
    heading(doc, "3", "御社名が届く相手", "地域の子育て世帯と、野球を応援する人たちに、毎週届きます。")
    table(doc, [
        ["届く相手", "規模", "接点"],
        ["部員の家庭", "130名", "月28,000円の会費で週4回通う家庭。練習の送迎・試合観戦で毎週チームに関わります"],
        ["Instagram", "2,088人", "フォロワー（2026年11月3日）。直近3か月の表示回数 614,400回"],
        ["Facebook", "2,619人", "フォロワー（2026年11月3日）。直近3か月の表示回数 78,745回"],
        ["試合会場", "毎週末", "対戦チームの選手・保護者、大会関係者。遠征は東海地区・全国大会まで"],
        ["地域", "2市", "埼玉県狭山市（入曽地区）と東京都東大和市。両チームの地元で掲出されます"],
    ], [30, 26, 114])
    para(doc, "**反響の大きかった投稿（Instagram・投稿1本あたり）**", after=2)
    table(doc, [
        ["投稿日", "内容", "表示回数", "リーチ"],
        ["2026年10月22日", "OB吉田健吾選手のドラフト指名", "63,384回", "33,362人"],
        ["2026年8月10日", "甲子園で戦うOBたちへの激励", "71,272回", "32,059人"],
        ["2026年10月1日", "侍ジャパンU15 ドミニカ共和国戦に在籍2名がスタメン", "51,057回", "24,465人"],
        ["2026年8月9日", "甲子園でOB2名がスタメン", "46,123回", "21,950人"],
        ["2026年8月12日", "花咲徳栄のスタメンにOB4名", "43,597回", "19,335人"],
    ], [33, 79, 29, 29])
    note(doc, "出典：Metricool（Instagram Feed Posts、2026年8月5日〜11月4日の14投稿）。1投稿あたりのリーチは平均15,608人、最も少ない投稿でも5,954人でした。表示回数は延べ回数、リーチは見た人の数です。")

    # 4. メリット
    heading(doc, "4", "御社にとってのメリット", "目的に合わせてお使いいただけます。")
    table(doc, [
        ["御社の目的", "当チームでできること", "向いている業種の例"],
        ["地元での認知・集客", "ユニフォーム・横断幕・SNSでの社名露出。保護者向けに御社の特典（割引など）をご案内", "整骨院・接骨院、学習塾、自動車販売・整備、住宅・不動産、飲食"],
        ["採用・人材確保", "「地域の子どもを応援する会社」として採用広報に使える写真・実績。活動報告書をそのまま会社案内に", "建設、製造、運輸、介護・医療"],
        ["社会貢献・企業価値", "協賛の実績と使い道を年度末に報告書で提出。地域貢献の取り組みとして公表いただけます", "金融、地場の中堅企業"],
        ["社員の福利厚生", "元プロ指導陣による社員ご家族向けの野球教室（トップパートナー特典）", "従業員の多い企業"],
    ], [34, 84, 52])

    # 5. プラン
    heading(doc, "5", "協賛プラン", "4つのプランからお選びください（金額は年額・税込）。")
    table(doc, [
        ["特典", "トップパートナー\n500,000円\n1社限定", "オフィシャル\nパートナー\n200,000円\n3社", "サポート\nカンパニー\n50,000円\n10社", "応援団\n10,000円\n個人・個人事業主"],
        ["両チーム公式ユニフォーム袖へのロゴ", "◎", "－", "－", "－"],
        ["練習着へのロゴ", "○", "○", "－", "－"],
        ["試合会場の横断幕へのロゴ", "○", "○", "○", "－"],
        ["公式サイトへのロゴ・リンク掲載", "○", "○", "○", "お名前"],
        ["SNSでのご紹介（Instagram・Facebook）", "月2回", "年6回", "年2回", "年1回"],
        ["保護者130家庭への特典のご案内", "年4回", "年2回", "年1回", "－"],
        ["元プロ指導陣による社員家族向け野球教室", "年1回", "－", "－", "－"],
        ["効果データ付き活動報告書", "四半期ごと", "年2回", "年1回", "年1回"],
        ["感謝状の贈呈", "○", "○", "○", "－"],
    ], [58, 30, 28, 28, 26], center_cols=(1, 2, 3, 4), size=9)
    note(doc, "◎は二チーム（狭山西武ボーイズ・東大和狭山ボーイズ）両方への掲出です。公式戦でのユニフォーム掲出は、各大会の要項に沿って行います。")
    para(doc, "**費用の目安**", after=2)
    table(doc, [
        ["比べるもの", "1人に届ける費用", "根拠"],
        ["当チームSNSでのご紹介（トップパートナー）", "約3.5円", "年24回×1回あたり6,000人（直近14投稿で最も少なかったリーチ5,954人を基準に控えめに試算）＝144,000人。500,000円÷144,000人"],
        ["新聞折込チラシ", "約7円", "1枚を家庭に届けるリーチ単価の目安（宣伝会議 AdverTimes 掲載の折込会社談話、2022年）"],
    ], [52, 28, 90])
    note(doc, "SNSのご紹介投稿は、ユニフォーム・横断幕・公式サイトでの露出とは別に数えています。試算は過去の実績にもとづくもので、将来の表示回数を保証するものではありません。")

    # 6. 進め方
    heading(doc, "6", "お申込みから掲出まで")
    table(doc, [
        ["時期", "内容"],
        ["2026年12月〜2027年1月", "お申込み・協賛契約書の取り交わし・ロゴデータのご提供"],
        ["2027年2月〜3月", "ユニフォーム・練習着・横断幕の製作、ご請求書の発行・お振込み"],
        ["2027年4月", "新年度の活動開始とともに掲出。SNSで協賛企業様をご紹介"],
        ["2027年7月・10月・2028年1月", "活動報告書（SNSの表示回数・ご紹介投稿のリーチ）をお届け"],
        ["2028年3月", "年間報告書の提出と、次年度のご相談"],
    ], [52, 118])
    para(doc, "**効果は数字でご報告します。** SNSの表示回数とリーチは分析ツール（Metricool）で毎月集計し、ご紹介投稿ごとの数値を報告書に載せます。", after=6)

    # 7. Q&A
    heading(doc, "7", "よくいただくご質問")
    table(doc, [
        ["ご質問", "回答"],
        ["経理上はどう扱えばよいですか", "ロゴ掲出などの広告の見返りがある協賛は、広告宣伝費として扱える場合があります。見返りがない場合は寄附金となり、損金算入に限度があります（法人税法第37条、国税庁タックスアンサーNo.5281）。最終的なご判断は貴社の税理士様にご確認ください。"],
        ["インボイス（適格請求書）は出ますか", "当チームの登録状況は、ご契約時に書面でお知らせします。未登録の事業者からの仕入れは、2026年10月1日〜2029年9月30日の間、仕入税額の50％が控除の対象です（国税庁「適格請求書等保存方式の概要」）。"],
        ["協賛金は何に使われますか", "遠征費・用具費・グラウンド整備費など、選手の活動に充て、保護者の負担を抑えます。使い道は年間報告書でご報告します。"],
        ["子どもの写真は使えますか", "保護者の同意が確認できた写真に限り、当チームの投稿を貴社アカウントでシェアいただけます。選手の氏名・学校名は掲載しません。"],
        ["途中で解約できますか", "年度単位のご契約です。ご事情がある場合はご相談ください。"],
        ["分割払いはできますか", "トップパートナー・オフィシャルパートナーは、前期・後期の2回払いも承ります。"],
    ], [44, 126])

    page_break(doc)
    # 8. 会長から
    heading(doc, "8", "会長からのご挨拶")
    para(doc, "私はかつてプロ野球の世界に身を置き、その経験のすべてを注ぎ込んで2013年に当チームを創設いたしました。月刊誌『致知』に「一道を極めた人は、必ず人物になる」という言葉があります。私たちが育てたいのは、野球を通じて、社会に出たときに必要とされる人間です。", after=4)
    para(doc, "この10月、卒団生が初めてプロ野球の世界へ進みました。後に続く子どもたちが、費用の心配なく全国の舞台に挑めるよう、地域の皆様のお力をお借りしたいと考えております。何卒よろしくお願い申し上げます。", after=4)
    para(doc, "狭山西武ボーイズ　会長　小野　剛", 10, True, align=WD_ALIGN_PARAGRAPH.RIGHT, after=8)

    # 9. お申込み
    heading(doc, "9", "お申込み・お問い合わせ")
    table(doc, [
        ["項目", "内容"],
        ["お申込み方法", "お電話またはメールでご連絡ください。協賛契約書とご請求書をお送りします"],
        ["お振込先", bank or "ご請求書に記載いたします"],
        ["窓口", "狭山西武ボーイズ 事務局（埼玉県狭山市南入曽448-3）"],
        ["電話／FAX", "TEL 04-2968-6727　／　FAX 04-2968-6728"],
        ["メール", "onogo@sayamaseibu.com"],
    ], [34, 136])
    para(doc, "まずは15分ほど、ご説明のお時間をいただけますと幸いです。平日夜の練習（19:00〜22:00）も、いつでもご見学いただけます。", 10.5, True, NAVY, before=4)

    doc.save(path)
    print("作成しました:", os.path.relpath(path, ROOT))


if __name__ == "__main__":
    os.makedirs(os.path.join(ROOT, "output"), exist_ok=True)
    build(os.path.join(ROOT, "output", "協賛提案書_2027年度.docx"), bank_text())
    build(os.path.join(ROOT, "business", "協賛提案書_2027年度_見本.docx"), None)
