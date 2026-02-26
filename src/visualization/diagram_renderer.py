import json
import re
import io
from typing import Optional, List, Dict


def extract_json_from_llm(text: str) -> Optional[dict]:
    """Try to extract a JSON block from LLM output."""
    json_block = re.search(r"```json\s*([\s\S]*?)```", text, re.IGNORECASE)
    if json_block:
        raw = json_block.group(1).strip()
    else:
        raw_match = re.search(r"\{[\s\S]*\s*\}", text)
        if raw_match:
            raw = raw_match.group(0)
        else:
            return None
    try:
        # cleanup potential trailing commas
        cleaned = re.sub(r",\s*\}", "}", raw)
        cleaned = re.sub(r",\s*\]", "]", cleaned)
        return json.loads(cleaned)
    except Exception:
        return None


def build_roadmap_html(data: dict, title: str) -> str:
    """Build a beautiful Horizontal snake-style Roadmap infographic."""
    nodes = data.get("nodes", [])
    if not nodes:
        return "<h3>No data found to display.</h3>"

    # Define icons based on type
    icons = {
        "entry": "🚀",
        "module": "📦",
        "class": "🏗️",
        "function": "⚙️",
        "database": "💾",
        "external": "🌐",
        "test": "🧪",
        "default": "🔹"
    }
    
    colors = ["#FF6B6B", "#4D96FF", "#6BCB77", "#FFD93D", "#9D174D", "#9B59B6", "#F0A500"]

    # Limit to 8 nodes for the roadmap to keep it clean
    display_nodes = nodes[:8]

    # Generate stations HTML
    stations_html = ""
    for i, n in enumerate(display_nodes):
        ntype = n.get("type", "default")
        icon = icons.get(ntype, icons["default"])
        color = colors[i % len(colors)]
        label = n.get("label", "Component")
        desc = n.get("description", "")
        
        stations_html += f"""
        <div class="card-item" style="--accent: {color}">
            <div class="card-header">
                <span class="icon">{icon}</span>
                <span class="step-num">{i+1}</span>
            </div>
            <div class="card-body">
                <h3>{label}</h3>
                <p>{desc}</p>
            </div>
        </div>
        """

    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8"/>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;700;900&display=swap" rel="stylesheet"/>
    <style>
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{ 
            background: #0D1117; 
            font-family: 'Outfit', sans-serif; 
            color: #C9D1D9;
            padding: 30px 40px 100px 40px;
            scroll-behavior: smooth;
            overflow-x: hidden;
        }}
        
        .header {{
            text-align: left;
            margin-bottom: 40px;
            border-left: 5px solid #58A6FF;
            padding-left: 20px;
            margin-top: 10px;
        }}
        .header h1 {{
            font-size: 32px;
            font-weight: 900;
            color: #F0F6FC;
            margin-bottom: 5px;
        }}
        .header p {{ color: #8B949E; font-size: 16px; }}

        .roadmap-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 30px;
            position: relative;
            padding-bottom: 60px;
        }}

        .card-item {{
            background: #161B22;
            border: 1px solid #30363D;
            border-radius: 20px;
            overflow: hidden;
            transition: 0.3s;
            position: relative;
            display: flex;
            flex-direction: column;
            box-shadow: 0 4px 15px rgba(0,0,0,0.4);
        }}
        
        .card-item:hover {{
            transform: translateY(-8px);
            border-color: var(--accent);
            box-shadow: 0 12px 30px rgba(0,0,0,0.5);
        }}

        .card-header {{
            background: var(--accent);
            padding: 16px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .icon {{ font-size: 28px; }}
        .step-num {{
            font-size: 18px;
            font-weight: 900;
            color: rgba(0,0,0,0.4);
        }}

        .card-body {{
            padding: 22px;
            flex-grow: 1;
        }}

        .card-body h3 {{
            font-size: 18px;
            font-weight: 700;
            color: #F0F6FC;
            margin-bottom: 10px;
        }}

        .card-body p {{
            color: #8B949E;
            font-size: 14px;
            line-height: 1.6;
        }}

        /* Subtle glow background */
        .glow {{
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: radial-gradient(circle at 10% 10%, rgba(88,166,255,0.05) 0%, transparent 50%),
                        radial-gradient(circle at 90% 90%, rgba(139,92,246,0.05) 0%, transparent 50%);
            z-index: -1;
            pointer-events: none;
        }}
    </style>
</head>
<body>
    <div class="glow"></div>
    <div class="header">
        <h1>{title}</h1>
        <p>A high-level view of how the system works</p>
    </div>

    <div class="roadmap-grid">
        {stations_html}
    </div>
</body>
</html>"""


def render_architecture_diagram(llm_answer: str, title: str = "Project Roadmap") -> Optional[str]:
    data = extract_json_from_llm(llm_answer)
    if not data or "nodes" not in data: return None
    return build_roadmap_html(data, title)


def render_from_data(data: dict, title: str = "Project Roadmap") -> Optional[str]:
    if not data or "nodes" not in data: return None
    return build_roadmap_html(data, title)
