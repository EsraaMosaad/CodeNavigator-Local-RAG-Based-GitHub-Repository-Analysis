"""
repo_scanner.py
Scans an actual repository on disk using AST and produces
a vis.js-ready JSON graph of the real code structure.
"""
import os
import ast
import json
import re
from typing import Optional, List, Dict, Tuple


# ── helpers ────────────────────────────────────────────────────────────────

def _short(name: str, limit: int = 22) -> str:
    return name if len(name) <= limit else name[:limit - 1] + "…"


def _sanitize_id(text: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_]", "_", text)


# ── AST scanning ───────────────────────────────────────────────────────────

def scan_repo(repo_path: str) -> dict:
    """
    Walk repo_path, parse every .py file with AST,
    and return {"nodes": [...], "edges": [...]} ready for vis.js.
    """
    nodes: List[dict] = []
    edges: List[dict] = []
    seen_ids: set = set()

    # Map module_path → node_id for edge building
    module_ids: Dict[str, str] = {}

    py_files = []
    for root, dirs, files in os.walk(repo_path):
        # Skip hidden / cache dirs
        dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__"]
        for fname in files:
            if fname.endswith(".py"):
                py_files.append(os.path.join(root, fname))

    for fpath in py_files:
        rel = os.path.relpath(fpath, repo_path)
        module_name = rel.replace(os.sep, ".").removesuffix(".py")
        mod_id = _sanitize_id(module_name)

        # Determine node type
        if rel in ("app.py", "main.py", "run.py", "__main__.py"):
            ntype = "entry"
        elif rel.startswith("test") or "/test" in rel:
            ntype = "test"
        else:
            ntype = "module"

        # Parse AST
        try:
            src = open(fpath, "r", encoding="utf-8", errors="ignore").read()
            tree = ast.parse(src)
            # Module docstring
            mod_doc = ast.get_docstring(tree) or ""
        except SyntaxError:
            continue

        if mod_id not in seen_ids:
            nodes.append({
                "id": mod_id,
                "label": _short(rel),
                "type": ntype,
                "description": mod_doc[:200] if mod_doc else rel,
            })
            seen_ids.add(mod_id)
            module_ids[rel] = mod_id

        # Extract classes
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                cid = _sanitize_id(f"{module_name}__{node.name}")
                if cid not in seen_ids:
                    class_doc = ast.get_docstring(node) or ""
                    nodes.append({
                        "id": cid,
                        "label": _short(node.name),
                        "type": "class",
                        "description": class_doc[:150] if class_doc else f"class in {rel}",
                    })
                    seen_ids.add(cid)
                    edges.append({"from": mod_id, "to": cid, "label": "defines"})

                # Base classes → inheritance edges
                for base in node.bases:
                    try:
                        base_name = ast.unparse(base)
                    except:
                        base_name = ""
                    if base_name:
                        base_id = _sanitize_id(base_name)
                        if base_id in seen_ids:
                            edges.append({"from": cid, "to": base_id, "label": "extends"})

            # Top-level functions only
            elif isinstance(node, ast.FunctionDef):
                # Check for module level parent
                parent = getattr(node, "_parent", None)
                if isinstance(parent, ast.Module):
                    fid = _sanitize_id(f"{module_name}__{node.name}")
                    if fid not in seen_ids:
                        nodes.append({
                            "id": fid,
                            "label": _short(f"{node.name}()"),
                            "type": "function",
                            "description": f"function in {rel}",
                        })
                        seen_ids.add(fid)
                        edges.append({"from": mod_id, "to": fid, "label": "defines"})

        # Manually track parents for functions
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                child._parent = node

        # Extract imports
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                target_parts = node.module.split(".")
                for rel_other, other_id in module_ids.items():
                    other_parts = os.path.splitext(rel_other)[0].replace(os.sep, ".").split(".")
                    if target_parts[-1] == other_parts[-1] or node.module.endswith(other_parts[-1]):
                        if mod_id != other_id:
                            edges.append({"from": mod_id, "to": other_id, "label": "imports"})
                        break

    # Prune
    connected_ids = {e["from"] for e in edges} | {e["to"] for e in edges}
    entry_ids = {n["id"] for n in nodes if n["type"] in ("entry", "module")}
    keep = connected_ids | entry_ids
    nodes = [n for n in nodes if n["id"] in keep]

    return {"nodes": nodes, "edges": edges}
