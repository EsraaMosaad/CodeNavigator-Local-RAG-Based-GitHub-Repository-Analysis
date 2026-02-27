import streamlit as st
import streamlit.components.v1 as components
import re

def sanitize_mermaid(code: str) -> str:
    """Sanitize syntax for diagram rendering."""
    # Remove any lingering markdown blocks inside the content
    code = re.sub(r'```mermaid\n?|```', '', code, flags=re.IGNORECASE)
    
    # Common error: nested or unquoted brackets in labels [Label [extra]]
    # This regex looks for patterns like ID[Label] and ensures they are safely handled
    # A simplified approach to fix most common flowchart label errors:
    lines = []
    for line in code.split('\n'):
        # Escape any potential HTML characters
        clean_line = line.replace('<', '&lt;').replace('>', '&gt;')
        
        # Heuristic: If a line has a bracket label like A[...], ensure it doesn't have nested unquoted brackets
        # Mermaid is picky about [ ] inside labels unless the whole label is quoted
        if '[' in clean_line and ']' in clean_line:
            match = re.search(r'(\w+)\[(.*?)\]', clean_line)
            if match:
                node_id, label = match.groups()
                if '[' in label or ']' in label: # Nested brackets found
                    # Replace with a version that avoids the crash
                    safe_label = label.replace('[', '(').replace(']', ')')
                    clean_line = clean_line.replace(f'[{label}]', f'["{safe_label}"]')
        
        lines.append(clean_line)
    
    return '\n'.join(lines).strip()

def render_mermaid(answer: str):
    """Parses text and renders both markdown parts and visual Mermaid diagrams in their original order."""
    mermaid_pattern = re.compile(r"(```mermaid\s*[\s\S]*?```)", re.IGNORECASE)
    parts = mermaid_pattern.split(answer)
    
    diagram_count = 0
    for part in parts:
        if part.lower().strip().startswith("```mermaid"):
            # This is a mermaid block
            diagram_code = re.sub(r"```mermaid\s*|```", "", part, flags=re.IGNORECASE).strip()
            sanitized_code = sanitize_mermaid(diagram_code)
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
            <style>
              body, html {{ margin:0; padding:0; background:transparent; overflow:hidden; font-family:'Inter', sans-serif; }}
              .wrap {{ 
                background: #111118; 
                border: 1px solid rgba(255,255,255,0.08); 
                border-radius: 12px; 
                padding: 30px; 
                margin: 10px 0;
                box-shadow: 0 10px 40px rgba(0,0,0,0.4);
              }}
              .mermaid {{ visibility: hidden; }}
              .mermaid[data-processed="true"] {{ visibility: visible; }}
            </style>
            </head>
            <body>
              <div class="wrap">
                <pre class="mermaid">
{sanitized_code}
                </pre>
              </div>
              <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
              <script>
                mermaid.initialize({{ 
                  startOnLoad: true, 
                  theme: 'dark',
                  securityLevel: 'loose',
                  themeVariables: {{
                    primaryColor: '#6366F1',
                    primaryTextColor: '#FAFAFA',
                    lineColor: '#A5B4FC',
                    mainBkg: '#18181B',
                    nodeBorder: 'rgba(255,255,255,0.1)'
                  }}
                }});
              </script>
            </body></html>
            """
            components.html(html, height=650, scrolling=True)
            diagram_count += 1
        elif part.strip():
            # This is regular markdown text
            st.markdown(part)
    return diagram_count > 0

def render_sidebar_branding():
    """Persistent sidebar branding logo and wordmark."""
    st.markdown("""
    <div style="display:flex; align-items:center; gap:10px; padding:4px 4px 12px;">
        <div style="width:32px; height:32px; background:linear-gradient(135deg,#6366F1,#8B5CF6);
                    border-radius:8px; display:flex; align-items:center; justify-content:center;
                    font-size:16px;">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="16 18 22 12 16 6"></polyline>
                <polyline points="8 6 2 12 8 18"></polyline>
            </svg>
        </div>
        <div>
            <div style="color:#FAFAFA; font-weight:700; font-size:14px; line-height:1;">CodeNavigator</div>
            <div style="color:#71717A; font-size:11px; margin-top:2px;">Repository Analytics</div>
        </div>
    </div>
    <hr style="border:none; border-top:1px solid rgba(255,255,255,0.07); margin:0 0 16px 0;">
    """, unsafe_allow_html=True)

def render_hero():
    """Empty state hero section."""
    st.markdown("""
    <div style="display:flex; flex-direction:column; align-items:center; justify-content:center;
                padding:80px 20px; text-align:center;">
        <div style="width:64px; height:64px; background:linear-gradient(135deg,#6366F1,#8B5CF6);
                    border-radius:16px; display:flex; align-items:center; justify-content:center;
                    margin-bottom:20px; box-shadow:0 0 30px rgba(99,102,241,0.3);">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="16 18 22 12 16 6"></polyline>
                <polyline points="8 6 2 12 8 18"></polyline>
            </svg>
        </div>
        <h2 style="color:#FAFAFA; font-family:'Inter',sans-serif; font-weight:700;
                   font-size:22px; margin:0 0 8px; letter-spacing:-0.3px;">Repository Analytics Interface</h2>
        <p style="color:#71717A; font-size:14px; max-width:400px; line-height:1.6; margin:0 0 28px;">
            Input a repository URL in the sidebar and select
            <strong style='color:#A5B4FC;'>Initialize Analysis</strong>
            to generate an architectural overview.
        </p>
        <div style="display:flex; gap:10px; flex-wrap:wrap; justify-content:center;">
            <div style="background:#111118; border:1px solid rgba(255,255,255,0.07); border-radius:8px;
                        padding:10px 16px; font-size:13px; color:#A1A1AA; display:flex; align-items:center; gap:8px;">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
                Summarize codebase
            </div>
            <div style="background:#111118; border:1px solid rgba(255,255,255,0.07); border-radius:8px;
                        padding:10px 16px; font-size:13px; color:#A1A1AA; display:flex; align-items:center; gap:8px;">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
                Identify potential issues
            </div>
            <div style="background:#111118; border:1px solid rgba(255,255,255,0.07); border-radius:8px;
                        padding:10px 16px; font-size:13px; color:#A1A1AA; display:flex; align-items:center; gap:8px;">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6"></polygon><line x1="8" y1="2" x2="8" y2="18"></line><line x1="16" y1="6" x2="16" y2="22"></line></svg>
                Map architecture
            </div>
            <div style="background:#111118; border:1px solid rgba(255,255,255,0.07); border-radius:8px;
                        padding:10px 16px; font-size:13px; color:#A1A1AA; display:flex; align-items:center; gap:8px;">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
                Interactive code query
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
