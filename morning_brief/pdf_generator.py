"""
pdf_generator.py – Institutional Fund PDF Reporting Engine.
Features: Market Dashboard, Sector Dossiers, and Trade Invalidation Tracking.
"""

from datetime import datetime
from typing import Optional
import os

from reportlab.lib.pagesizes import LETTER
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
)
from reportlab.lib.units import inch

# ── Styling ──────────────────────────────────────────────────────────────────

styles = getSampleStyleSheet()
style_h1 = ParagraphStyle(
    "H1", parent=styles["Heading1"], fontSize=26, textColor=colors.HexColor("#0D47A1"),
    spaceAfter=10, fontName="Helvetica-Bold"
)
style_h2 = ParagraphStyle(
    "H2", parent=styles["Heading2"], fontSize=18, textColor=colors.HexColor("#1565C0"),
    spaceBefore=15, spaceAfter=10, fontName="Helvetica-Bold"
)
style_h3 = ParagraphStyle(
    "H3", parent=styles["Heading3"], fontSize=13, textColor=colors.HexColor("#1976D2"),
    spaceBefore=8, spaceAfter=5, fontName="Helvetica-Bold"
)
style_body = ParagraphStyle(
    "Body", parent=styles["Normal"], fontSize=9.5, leading=13, spaceAfter=6
)
style_dashboard = ParagraphStyle(
    "Dashboard", parent=styles["Normal"], fontSize=10, leading=14, alignment=1, fontName="Helvetica-Bold"
)
style_meta = ParagraphStyle(
    "Meta", parent=styles["Normal"], fontSize=8.5, textColor=colors.grey
)
style_bullet = ParagraphStyle(
    "Bullet", parent=styles["Normal"], fontSize=9.5, leading=13, leftIndent=15, spaceAfter=4
)

def get_sentiment_tag(score: float):
    """0-100 Scale Tags"""
    if score >= 75: return "STRONG BULLISH", colors.HexColor("#1B5E20")
    if score >= 60: return "BULLISH", colors.HexColor("#4CAF50")
    if score >= 40: return "NEUTRAL", colors.HexColor("#9E9E9E")
    if score >= 25: return "BEARISH", colors.HexColor("#E57373")
    return "DISTRESSED/BEARISH", colors.HexColor("#B71C1C")

def format_pct(val: float) -> str:
    color = "green" if val >= 0 else "red"
    return f"<font color='{color}'>{val:+.2f}%</font>"

# ── PDF Builder ───────────────────────────────────────────────────────────────

def generate_pdf(analysis: dict, market_data: dict, output_path: Optional[str] = None):
    """
    Constructs the premium institutional report.
    """
    if not output_path:
        from config import OUTPUT_DIR
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
        import os
        output_path = os.path.join(OUTPUT_DIR, f"apeiro_brief_{timestamp}.pdf")

    doc = SimpleDocTemplate(output_path, pagesize=LETTER, leftMargin=0.5*inch, rightMargin=0.5*inch)
    story = []

    # 1. INSTITUTIONAL HEADER
    date_str = datetime.now().strftime("%B %d, %Y | %H:%M EST")
    story.append(Paragraph("APEIRO INVESTMENTS", style_h1))
    story.append(Paragraph(f"GLOBAL MARKET INTELLIGENCE BRIEF", style_body))
    story.append(Paragraph(f"FOR INTERNAL USE ONLY | {date_str}", style_meta))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0D47A1"), spaceBefore=5, spaceAfter=10))

    # 2. MARKET DASHBOARD (Page 1 Top)
    dash = market_data.get("dashboard", {})
    macro = market_data.get("macro", {})
    
    # Dashboard Row: SPY | QQQ | VIX | 10Y-2Y
    spy = dash.get("SPY", {"price": 0, "change": 0})
    qqq = dash.get("QQQ", {"price": 0, "change": 0})
    vix = dash.get("^VIX", {"price": 0, "change": 0})
    ten_two = macro.get("ten_two_spread", 0)
    
    dash_text = (
        f"S&P 500: {spy['price']:.2f} ({format_pct(spy['change'])})  |  "
        f"Nasdaq: {qqq['price']:.2f} ({format_pct(qqq['change'])})  |  "
        f"VIX: {vix['price']:.2f}  |  "
        f"10Y-2Y Spread: {ten_two:+.3f}"
    )
    story.append(Paragraph(dash_text, style_dashboard))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey, spaceBefore=4, spaceAfter=8))

    # 3. EXECUTIVE SUMMARY
    story.append(Paragraph("Executive Summary & Institutional Narrative", style_h2))
    story.append(Paragraph(analysis.get("market_tone", "No executive summary provided."), style_body))
    
    # 4. TACTICAL TRADE IDEAS (Page 1 Bottom)
    story.append(Paragraph("Tactical Trade Ideas & Accountability Tracker", style_h3))
    trades = analysis.get("trade_ideas", [])
    if trades:
        data = [["Asset", "Type", "View", "Rationale & Invalidation", "Horizon"]]
        for t in trades:
            desc = f"<b>Rationale:</b> {t.get('rationale')}<br/><b>Invalidation:</b> {t.get('invalidation')}"
            
            # Wrap Asset, Type, and View in Paragraphs to prevent overflow
            asset_para = Paragraph(t.get("asset", "N/A"), style_meta)
            type_para = Paragraph(t.get("type", "N/A"), style_meta)
            view_para = Paragraph(t.get("view", "N/A"), style_meta)
            
            data.append([asset_para, type_para, view_para, Paragraph(desc, style_meta), t.get("horizon")])
        
        # Professional column re-balancing: 
        # Asset(0.9\"), Type(0.6\"), View(0.6\"), Rationale(4.5\"), Horizon(0.9\")
        t = Table(data, colWidths=[0.9*inch, 0.6*inch, 0.6*inch, 4.5*inch, 0.9*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#F5F5F5")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor("#0D47A1")),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 9),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
            ('BOX', (0,0), (-1,-1), 0.5, colors.lightgrey),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(t)
    
    story.append(PageBreak())

    # 5. SECTOR DOSSIERS
    story.append(Paragraph("Sector Strategic Intelligence", style_h2))
    sectors = analysis.get("sectors", {})
    for name, data in sectors.items():
        score = data.get("score", 50)
        tag, tag_color = get_sentiment_tag(score)
        
        # Sector Header with "Sentiment Gauge"
        story.append(Paragraph(f"{name} Sector Dossier", style_h3))
        story.append(Paragraph(f"<b>INDEX SCORE: {score}/100</b> — <font color='{tag_color}'>{tag}</font>", style_body))
        
        story.append(Paragraph("<b>Equity & Growth Outlook</b>", style_body))
        story.append(Paragraph(data.get("equity_outlook", "N/A"), style_body))
        
        story.append(Paragraph("<b>Credit & Solvency Analysis</b>", style_body))
        story.append(Paragraph(data.get("credit_outlook", "N/A"), style_body))
        
        # Descriptive Niche Analysis
        niche = data.get("niche_signals", [])
        if niche:
            story.append(Paragraph("<b>Forensic Niche Analysis</b>", style_body))
            for item in niche:
                sig = item.get("signal", "N/A")
                desc = item.get("description", "N/A")
                story.append(Paragraph(f"• <b>{sig}</b>: {desc}", style_bullet))
        
        # Article Score Methodology
        articles = data.get("article_sentiments", [])
        if articles:
            story.append(Paragraph(f"<b>Forensic Evidence ({len(articles)} articles scanned)</b>", style_meta))
            for art in articles[:4]:
                s = art.get('sentiment', 0)
                icon = "▲" if s > 0 else "▼" if s < 0 else "—"
                color = "green" if s > 0 else "red" if s < 0 else "grey"
                story.append(Paragraph(f"<font color='{color}'>{icon}</font> {art.get('title')}", style_meta))

        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.whitesmoke, spaceBefore=10, spaceAfter=10))

    # FOOTER
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph("CONFIDENTIAL RESEARCH | APEIRO INVESTMENTS", ParagraphStyle("Footer", parent=style_meta, alignment=1)))

    doc.build(story)
    return output_path
