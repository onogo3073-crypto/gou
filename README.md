# 球団運営AIエージェント

狭山西武ボーイズ・福島ピーチフェニックスの運営文書（募集・保護者連絡・スポンサー・試合報告・会計）を作る Claude Code 用エージェントです。

## 使い方
1. `.claude/skills/kyudan-assistant/references/team_profile.md` の「要記入」を埋めます。
2. このリポジトリを Claude Code で開き、「明日の練習中止をLINE用に」などと話しかけます。
3. Word が必要な時は「Wordで」と添えます（`tools/make_docx.py` で MSゴシック10pt の文書を出力）。

詳しくは `docs/球団運営AIエージェント_導入ガイド.docx` をご覧ください。

## 収益化の仕組み
- 方針：`docs/収益化戦略_2026-11.docx`（スポンサー協賛→選手募集→AI運営パッケージ外販の順）
- 営業管理：`business/sponsor_pipeline.md`・`business/kpi.md`。「今週のスポンサー状況」と話しかけると次の行動を出します。
- 提案書：`python3 business/build_proposal.py` で作成（見本 `business/協賛提案書_2027年度_見本.docx`、振込先入りは `output/`）
