# Author: Vishal Bulbule
# Date: 2026-09-28

"""Research agent that writes a rich HTML infographic report and stores it as an artifact.

Flow: the user asks for research -> the root agent calls google_search
(model built-in grounding tool) -> the root agent extracts structured data
(key_metrics, bar_metrics, sections) -> `generate_html_report` renders a
beautiful self-contained HTML infographic with stat cards, animated progress
bars, and dark-theme styling, then calls `tool_context.save_artifact(...)`.

The artifact backend is not chosen here. It comes from the Runner / CLI:
    adk web --artifact_service_uri=memory://        # InMemoryArtifactService
    adk web --artifact_service_uri=gs://<bucket>    # GcsArtifactService

google_search is a model built-in tool and cannot share an agent with
function tools, so it lives in its own agent wrapped as an AgentTool.
"""

import re
from datetime import date

from google.adk.agents import LlmAgent
from google.adk.tools import ToolContext, google_search
from google.genai import types

MODEL = "gemini-3.5-flash"


# ---------------------------------------------------------------------------
# HTML builder
# ---------------------------------------------------------------------------

_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>{title}</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet"/>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    :root {{
      --bg:#0d1117; --surface:#161b22; --card:#1c2330; --border:#30363d;
      --accent1:#58a6ff; --accent2:#3fb950; --accent3:#f78166;
      --accent4:#d2a8ff; --accent5:#ffa657;
      --text:#e6edf3; --muted:#8b949e; --radius:14px;
    }}
    body {{ font-family:\'Inter\',sans-serif; background:var(--bg); color:var(--text); line-height:1.6; }}
    .report-header {{
      background:linear-gradient(135deg,#0d1117 0%,#161b22 40%,#1c2330 100%);
      border-bottom:1px solid var(--border); padding:56px 48px 40px; position:relative; overflow:hidden;
    }}
    .report-header::before {{
      content:\'\'; position:absolute; inset:0;
      background:radial-gradient(ellipse at 70% 50%,rgba(88,166,255,.08) 0%,transparent 60%),
                 radial-gradient(ellipse at 20% 80%,rgba(63,185,80,.06) 0%,transparent 50%);
      pointer-events:none;
    }}
    .badge {{
      display:inline-block; padding:4px 12px; border-radius:20px;
      background:rgba(88,166,255,.15); border:1px solid rgba(88,166,255,.3);
      color:var(--accent1); font-size:11px; font-weight:600;
      letter-spacing:1px; text-transform:uppercase; margin-bottom:18px;
    }}
    .report-header h1 {{
      font-size:clamp(28px,4vw,48px); font-weight:800; letter-spacing:-.5px;
      background:linear-gradient(90deg,#e6edf3 0%,#58a6ff 100%);
      -webkit-background-clip:text; -webkit-text-fill-color:transparent;
      background-clip:text; max-width:820px; line-height:1.2;
    }}
    .meta {{ margin-top:16px; color:var(--muted); font-size:13px; display:flex; gap:20px; flex-wrap:wrap; }}
    .container {{ max-width:1200px; margin:0 auto; padding:48px 32px; }}
    .stats-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:20px; margin-bottom:48px; }}
    .stat-card {{
      background:var(--card); border:1px solid var(--border); border-radius:var(--radius);
      padding:28px 24px; position:relative; overflow:hidden; transition:transform .2s,box-shadow .2s;
    }}
    .stat-card:hover {{ transform:translateY(-2px); box-shadow:0 8px 32px rgba(0,0,0,.4); }}
    .stat-card::before {{
      content:\'\'; position:absolute; top:0; left:0; right:0; height:3px;
      border-radius:var(--radius) var(--radius) 0 0;
    }}
    .stat-card:nth-child(1)::before {{ background:var(--accent1); }}
    .stat-card:nth-child(2)::before {{ background:var(--accent2); }}
    .stat-card:nth-child(3)::before {{ background:var(--accent3); }}
    .stat-card:nth-child(4)::before {{ background:var(--accent4); }}
    .stat-card:nth-child(5)::before {{ background:var(--accent5); }}
    .stat-label {{ font-size:11px; font-weight:600; letter-spacing:.8px; text-transform:uppercase; color:var(--muted); margin-bottom:10px; }}
    .stat-value {{ font-size:32px; font-weight:800; line-height:1; margin-bottom:6px; }}
    .stat-card:nth-child(1) .stat-value {{ color:var(--accent1); }}
    .stat-card:nth-child(2) .stat-value {{ color:var(--accent2); }}
    .stat-card:nth-child(3) .stat-value {{ color:var(--accent3); }}
    .stat-card:nth-child(4) .stat-value {{ color:var(--accent4); }}
    .stat-card:nth-child(5) .stat-value {{ color:var(--accent5); }}
    .stat-desc {{ font-size:12px; color:var(--muted); }}
    .section {{ background:var(--surface); border:1px solid var(--border); border-radius:var(--radius); margin-bottom:28px; overflow:hidden; }}
    .section-header {{ padding:20px 28px; border-bottom:1px solid var(--border); display:flex; align-items:center; gap:12px; }}
    .section-icon {{ width:36px; height:36px; border-radius:8px; display:flex; align-items:center; justify-content:center; font-size:18px; flex-shrink:0; }}
    .section-header h2 {{ font-size:18px; font-weight:700; color:var(--text); }}
    .section-body {{ padding:24px 28px; }}
    .section-body p {{ color:var(--muted); font-size:15px; margin-bottom:14px; }}
    .section-body p:last-child {{ margin-bottom:0; }}
    .insight-list {{ list-style:none; display:flex; flex-direction:column; gap:10px; }}
    .insight-list li {{
      display:flex; align-items:flex-start; gap:10px; font-size:14px; color:var(--muted);
      background:var(--card); border:1px solid var(--border); padding:12px 16px; border-radius:8px;
    }}
    .insight-list li::before {{ content:\'\u2192\'; color:var(--accent1); font-weight:700; flex-shrink:0; margin-top:1px; }}
    .bar-chart {{ display:flex; flex-direction:column; gap:14px; }}
    .bar-row {{ display:flex; flex-direction:column; gap:6px; }}
    .bar-meta {{ display:flex; justify-content:space-between; font-size:13px; }}
    .bar-label {{ color:var(--text); font-weight:500; }}
    .bar-val {{ color:var(--accent1); font-weight:700; }}
    .bar-track {{ height:10px; background:var(--card); border-radius:999px; overflow:hidden; border:1px solid var(--border); }}
    .bar-fill {{ height:100%; border-radius:999px; animation:grow 1s ease forwards; transform-origin:left; }}
    @keyframes grow {{ from{{ transform:scaleX(0); }} to{{ transform:scaleX(1); }} }}
    .sources-list {{ list-style:none; display:flex; flex-direction:column; gap:8px; }}
    .sources-list li {{ font-size:13px; padding:10px 14px; background:var(--card); border:1px solid var(--border); border-radius:8px; color:var(--muted); }}
    .sources-list li a {{ color:var(--accent1); text-decoration:none; }}
    .sources-list li a:hover {{ text-decoration:underline; }}
    .report-footer {{ text-align:center; padding:32px; color:var(--muted); font-size:12px; border-top:1px solid var(--border); margin-top:32px; }}
    .two-col {{ display:grid; grid-template-columns:1fr 1fr; gap:28px; margin-bottom:28px; }}
    @media(max-width:768px) {{ .two-col {{ grid-template-columns:1fr; }} }}
    .icon-blue   {{ background:rgba(88,166,255,.15); color:var(--accent1); }}
    .icon-green  {{ background:rgba(63,185,80,.15);  color:var(--accent2); }}
    .icon-red    {{ background:rgba(247,129,102,.15);color:var(--accent3); }}
    .icon-purple {{ background:rgba(210,168,255,.15);color:var(--accent4); }}
    .icon-orange {{ background:rgba(255,166,87,.15); color:var(--accent5); }}
  </style>
</head>
<body>
<header class="report-header">
  <div class="badge">&#128202; Research Report</div>
  <h1>{title}</h1>
  <div class="meta">
    <span>&#128197; Generated {gen_date}</span>
    <span>&#128279; Powered by Gemini + Google Search</span>
  </div>
</header>
<div class="container">
  {stat_cards_html}
  <div class="two-col">
    <div class="section" style="margin-bottom:0">
      <div class="section-header">
        <div class="section-icon icon-blue">&#128196;</div>
        <h2>Executive Summary</h2>
      </div>
      <div class="section-body">{exec_summary_html}</div>
    </div>
    <div class="section" style="margin-bottom:0">
      <div class="section-header">
        <div class="section-icon icon-green">&#128200;</div>
        <h2>Key Metrics at a Glance</h2>
      </div>
      <div class="section-body"><div class="bar-chart">{bar_chart_html}</div></div>
    </div>
  </div>
  {content_sections_html}
  {sources_section_html}
</div>
<footer class="report-footer">
  &#128202; Research Report &mdash; {title} &mdash; {gen_date} &mdash; Generated by ADK Research Agent
</footer>
</body>
</html>
"""

_SECTION_ICONS = ["&#128269;", "&#9889;", "&#128736;", "&#127919;", "&#128161;", "&#127758;"]
_ICON_CLASSES  = ["icon-blue", "icon-green", "icon-red", "icon-purple", "icon-orange", "icon-blue"]
_BAR_COLORS    = ["#58a6ff", "#3fb950", "#f78166", "#d2a8ff", "#ffa657"]
_BULLET_RE     = re.compile(r"^[-*]\s+")
_EM_DASH       = "\u2014"


def _para_or_bullets(text: str) -> str:
    """Convert a string with optional '- ' bullets into HTML."""
    lines   = text.strip().splitlines()
    bullets = [l.strip() for l in lines if re.match(r"^\s*[-*]\s+", l)]
    paras   = [l.strip() for l in lines if l.strip() and not re.match(r"^\s*[-*]\s+", l)]
    html = ""
    if paras:
        html += "".join(f"<p>{p}</p>" for p in paras)
    if bullets:
        items = "".join(f"<li>{_BULLET_RE.sub('', b)}</li>" for b in bullets)
        html += f'<ul class="insight-list">{items}</ul>'
    return html or f"<p>{text}</p>"


def _build_html(
    title: str,
    executive_summary: str,
    key_metrics: list,
    bar_metrics: list,
    sections: list,
    sources: list,
) -> str:
    """Render a rich self-contained HTML infographic report."""
    cards_html = '<div class="stats-grid">'
    for m in key_metrics[:5]:
        cards_html += (
            f'<div class="stat-card">'
            f'<div class="stat-label">{m.get("label", "Metric")}</div>'
            f'<div class="stat-value">{m.get("value", _EM_DASH)}</div>'
            f'<div class="stat-desc">{m.get("desc", "")}</div>'
            f'</div>'
        )
    cards_html += '</div>'

    bars_html = ""
    for i, bm in enumerate(bar_metrics[:6]):
        pct   = max(0, min(100, int(bm.get("pct", 50))))
        color = _BAR_COLORS[i % len(_BAR_COLORS)]
        bars_html += (
            f'<div class="bar-row">'
            f'<div class="bar-meta">'
            f'<span class="bar-label">{bm.get("label", "")}</span>'
            f'<span class="bar-val">{bm.get("value", "")}</span>'
            f'</div>'
            f'<div class="bar-track">'
            f'<div class="bar-fill" style="width:{pct}%;background:{color}"></div>'
            f'</div></div>'
        )
    if not bars_html:
        bars_html = "<p style='color:var(--muted)'>No bar metrics provided.</p>"

    content_html = ""
    for i, sec in enumerate(sections):
        icon     = _SECTION_ICONS[i % len(_SECTION_ICONS)]
        icon_cls = _ICON_CLASSES[i % len(_ICON_CLASSES)]
        body_html = _para_or_bullets(sec.get("body", ""))
        content_html += (
            f'<div class="section">'
            f'<div class="section-header">'
            f'<div class="section-icon {icon_cls}">{icon}</div>'
            f'<h2>{sec.get("heading", "Section")}</h2>'
            f'</div>'
            f'<div class="section-body">{body_html}</div>'
            f'</div>'
        )

    if sources:
        items = ""
        for i, s in enumerate(sources, 1):
            if s.startswith("http"):
                items += f'<li>[{i}] <a href="{s}" target="_blank">{s}</a></li>'
            else:
                items += f'<li>[{i}] {s}</li>'
        sources_html = (
            f'<div class="section">'
            f'<div class="section-header">'
            f'<div class="section-icon icon-purple">&#128279;</div>'
            f'<h2>Sources &amp; References</h2>'
            f'</div>'
            f'<div class="section-body"><ul class="sources-list">{items}</ul></div>'
            f'</div>'
        )
    else:
        sources_html = ""

    return _HTML_TEMPLATE.format(
        title=title,
        gen_date=date.today().isoformat(),
        stat_cards_html=cards_html,
        exec_summary_html=_para_or_bullets(executive_summary),
        bar_chart_html=bars_html,
        content_sections_html=content_html,
        sources_section_html=sources_html,
    )

# ---------------------------------------------------------------------------
# ADK Tools
# ---------------------------------------------------------------------------

async def generate_html_report(
    filename: str,
    title: str,
    executive_summary: str,
    key_metrics: list,
    bar_metrics: list,
    sections: list,
    sources: list,
    tool_context: ToolContext,
) -> dict:
    """Render a research report to a rich HTML infographic and save it as a versioned artifact.

    Args:
        filename: Artifact filename ending in .html, e.g. "gcp_ai_report.html".
        title: Report title shown at the top of the page.
        executive_summary: 2-4 sentence summary paragraph. May include '- ' bullet lines.
        key_metrics: Up to 5 dicts with keys 'label', 'value', 'desc'.
            Example: [{"label": "Market Size", "value": "$4.7T", "desc": "Global AI market 2025"}]
        bar_metrics: Up to 6 dicts with keys 'label', 'value', 'pct' (0-100 integer).
            Example: [{"label": "Cloud Adoption", "value": "78%", "pct": 78}]
        sections: List of dicts with 'heading' and 'body' (plain text or '- ' bullets).
            Suggested headings: Key Findings, Analysis, Trends, Challenges, Conclusion.
        sources: Source titles or URLs found during research (may be empty).
        tool_context: Injected by ADK; gives the tool access to artifacts.

    Returns:
        A dict with status, filename, saved version, and byte size.
    """
    if not filename.lower().endswith(".html"):
        filename += ".html"
    try:
        html_str = _build_html(
            title=title,
            executive_summary=executive_summary,
            key_metrics=key_metrics,
            bar_metrics=bar_metrics,
            sections=sections,
            sources=sources,
        )
    except Exception as exc:
        return {"status": "error", "error": f"HTML render failed: {exc}"}

    html_bytes = html_str.encode("utf-8")
    part = types.Part.from_bytes(data=html_bytes, mime_type="text/html")
    version = await tool_context.save_artifact(filename, part)
    return {
        "status": "ok",
        "filename": filename,
        "version": version,
        "bytes": len(html_bytes),
    }


async def list_reports(tool_context: ToolContext) -> dict:
    """List artifact filenames saved in this session.

    Args:
        tool_context: Injected by ADK; gives the tool access to artifacts.

    Returns:
        A dict with the list of artifact filenames.
    """
    return {"status": "ok", "artifacts": await tool_context.list_artifacts()}


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

root_agent = LlmAgent(
    model=MODEL,
    name="html_report_agent",
    description="Researches a topic on the web and produces a rich HTML infographic report artifact.",
    instruction=(
        "You are a research infographic report writer.\n"
        "1. When the user asks for research on a topic, call google_search with a focused "
        "query. Call it 2-3 more times for sub-topics (stats, trends, challenges) to gather "
        "rich data.\n"
        "2. From the research, extract:\n"
        "   a) key_metrics: 3-5 impressive headline stats (e.g. market size, growth rate, "
        "      adoption %) as {label, value, desc} dicts.\n"
        "   b) bar_metrics: 4-6 comparative figures (e.g. adoption by region, year-on-year "
        "      growth) as {label, value, pct} dicts where pct is an integer 0-100.\n"
        "   c) sections: 4-5 named sections (Key Findings, Analysis, Trends, Challenges, "
        "      Conclusion) each with a detailed 'body' using '- ' bullet lines for findings.\n"
        "   d) executive_summary: 3-4 sentence paragraph.\n"
        "3. Call generate_html_report with a snake_case filename ending in .html, the title, "
        "and all the structured data above.\n"
        "4. Reply with a 3-4 line summary and the filename + version saved. "
        "Do not paste the HTML into chat.\n"
        "If the user asks which reports exist, call list_reports."
    ),
    tools=[google_search, generate_html_report, list_reports],
)
