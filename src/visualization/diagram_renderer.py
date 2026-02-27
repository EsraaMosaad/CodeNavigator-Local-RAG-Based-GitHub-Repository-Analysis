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
        label = n.get("label", "Component")
        desc = n.get("description", "")
        
        stations_html += f"""
        <div class="card-item">
            <div class="badge">{i+1:02d}</div>
            <div class="card-body">
                <div class="card-title">
                    <span class="icon">{icon}</span>
                    <h3>{label}</h3>
                </div>
                <p>{desc}</p>
            </div>
        </div>
        """

    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8"/>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet"/>
    <style>
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{ 
            background: #0F1629; 
            font-family: 'Inter', sans-serif; 
            color: #F8FAFC;
            padding: 30px 40px 100px 40px;
            scroll-behavior: smooth;
            overflow-x: hidden;
        }}
        
        .header {{
            text-align: left;
            margin-bottom: 40px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            padding-bottom: 15px;
            margin-top: 10px;
        }}
        .header h1 {{
            font-size: 28px;
            font-weight: 700;
            color: #FFFFFF;
            margin-bottom: 5px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .header p {{ color: #94A3B8; font-size: 15px; }}

        .roadmap-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 20px;
            position: relative;
            padding-bottom: 60px;
        }}

        .card-item {{
            background: #1E2A45;
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-left: 3px solid #3B82F6;
            border-radius: 12px;
            position: relative;
            display: flex;
            flex-direction: column;
            transition: all 0.2s ease;
        }}
        
        .card-item:hover {{
            transform: translateY(-2px);
            border-color: rgba(59, 130, 246, 0.5);
            border-left: 4px solid #3B82F6;
            box-shadow: 0 10px 25px rgba(0,0,0,0.3);
        }}

        .badge {{
            position: absolute;
            top: 15px;
            right: 15px;
            font-size: 12px;
            font-weight: 600;
            color: #64748B;
            background: rgba(255, 255, 255, 0.05);
            padding: 4px 8px;
            border-radius: 6px;
        }}

        .card-body {{
            padding: 20px;
            flex-grow: 1;
            margin-top: 5px;
        }}

        .card-title {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 8px;
        }}

        .icon {{ font-size: 20px; }}

        .card-body h3 {{
            font-size: 16px;
            font-weight: 600;
            color: #FFFFFF;
        }}

        .card-body p {{
            color: #94A3B8;
            font-size: 14px;
            line-height: 1.5;
            margin-left: 30px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1><span class="icon">🗺️</span> {title}</h1>
        <p>A high-level logical view of the system architecture</p>
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
