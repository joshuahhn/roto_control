"""Embed user-facing project Markdown into a TouchDesigner component.

Execute this file inside TouchDesigner so ``textDAT`` and ``containerCOMP`` are
available in the caller's globals. Source Markdown is read only at build time;
the generated DATs contain inline snapshots with file syncing disabled.
"""

from __future__ import annotations

from pathlib import Path
import re


FUNCTION_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def _read_required(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"required project documentation is missing: {path}")
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        raise ValueError(f"project documentation is empty: {path}")
    return text


def read_project_docs(project_dir):
    """Read and validate every source before changing the TD network."""

    project_dir = Path(project_dir)
    result = {
        "readme": _read_required(project_dir / "README.md"),
        "overview": None,
        "functions": [],
    }

    docs_dir = project_dir / "docs"
    if not docs_dir.exists():
        return result

    result["overview"] = _read_required(docs_dir / "overview.md")
    functions_dir = docs_dir / "functions"
    if not functions_dir.is_dir():
        raise FileNotFoundError(f"required function docs directory is missing: {functions_dir}")
    function_files = sorted(functions_dir.glob("*.md"))
    if len(function_files) < 2:
        raise ValueError("complex project requires at least two function docs")
    for path in function_files:
        if not FUNCTION_RE.fullmatch(path.stem):
            raise ValueError(f"invalid function documentation filename: {path.name}")
        result["functions"].append((path.stem, _read_required(path)))
    return result


def _node(parent, kind, name):
    result = parent.op(name)
    if result is None:
        result = parent.create(kind, name)
    elif result.OPType != kind.__name__:
        raise RuntimeError(f"unexpected existing operator type at {result.path}")
    return result


def _write_text_dat(dat, text, source_label):
    dat.par.file.val = ""
    dat.par.syncfile.val = False
    dat.par.loadonstart.val = False
    dat.par.language.val = "text"
    dat.text = text
    dat.viewer = True
    dat.comment = f"Embedded snapshot of {source_label}; edit the Markdown source and rebuild."


def embed_project_docs(component, project_dir):
    """Create or update ``readme_md`` and optional complex-tool docs."""

    project_dir = Path(project_dir)
    content = read_project_docs(project_dir)

    readme = _node(component, textDAT, "readme_md")
    _write_text_dat(readme, content["readme"], "README.md")
    readme.nodeX, readme.nodeY = 0, -130
    readme.nodeWidth, readme.nodeHeight = 180, 120

    docs = None
    if content["overview"] is not None:
        docs = _node(component, containerCOMP, "docs")
        docs.viewer = True
        docs.nodeX, docs.nodeY = 220, -130
        docs.nodeWidth, docs.nodeHeight = 200, 140

        overview = _node(docs, textDAT, "overview_md")
        _write_text_dat(overview, content["overview"], "docs/overview.md")
        overview.nodeX, overview.nodeY = 0, 160

        index_lines = ["# Functions", ""]
        for function_name, _ in content["functions"]:
            index_lines.append(f"- `{function_name}` -> `fn_{function_name}_md`")
        index_dat = _node(docs, textDAT, "functions_md")
        _write_text_dat(index_dat, "\n".join(index_lines) + "\n", "docs/functions/")
        index_dat.nodeX, index_dat.nodeY = 220, 160

        for index, (function_name, text) in enumerate(content["functions"]):
            dat = _node(docs, textDAT, f"fn_{function_name}_md")
            _write_text_dat(dat, text, f"docs/functions/{function_name}.md")
            dat.nodeX = (index % 3) * 220
            dat.nodeY = -20 - (index // 3) * 150

    return {"readme_md": readme, "docs": docs}
