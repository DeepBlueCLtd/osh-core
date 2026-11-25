#!/usr/bin/env python3
"""
Verify that source references in the code-map docs still match the code.

Checks, for AGENTS.md and every .md file under docs/code-map/:
  1. Relative links resolve to an existing file or directory.
  2. Line anchors (#L12 or #L12-L20) are within the file's length.
  3. If the link text names a symbol (e.g. `EventBus.getPublisher()`), that
     symbol's last identifier appears within a few lines of the anchor.
     This catches anchors that drifted after code was edited.
  4. Backticked fully-qualified class names (`org.sensorhub.api.event.IEventBus`)
     resolve to a .java file somewhere in the repository.

Usage:  python3 docs/code-map/tools/check_refs.py      (run from repo root)
Exit code is non-zero if any reference is broken.
"""
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SLACK = 3  # lines of tolerance around an anchor when looking for the symbol

LINK_RE = re.compile(r"(?<!!)\[([^\]]+)\]\(([^)\s]+)\)")
ANCHOR_RE = re.compile(r"^L(\d+)(?:-L(\d+))?$")
FQCN_RE = re.compile(r"`((?:org|net|com)\.[a-z0-9_.]+\.[A-Z][A-Za-z0-9_]*)`")
IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def md_files():
    yield os.path.join(ROOT, "AGENTS.md")
    for d, _, files in os.walk(os.path.join(ROOT, "docs", "code-map")):
        for f in files:
            if f.endswith(".md"):
                yield os.path.join(d, f)


_java_index = None


def java_index():
    global _java_index
    if _java_index is None:
        _java_index = set()
        for d, dirs, files in os.walk(ROOT):
            dirs[:] = [x for x in dirs if x not in (".git", "build", ".gradle", "node_modules")]
            for f in files:
                if f.endswith(".java"):
                    rel = os.path.relpath(os.path.join(d, f), ROOT).replace(os.sep, "/")
                    _java_index.add(rel)
    return _java_index


def symbol_from_text(text):
    """Return the identifier to look for near an anchor, or None."""
    code = re.findall(r"`([^`]+)`", text)
    candidate = code[-1] if code else text
    candidate = re.sub(r"\(.*?\)", "", candidate)  # drop argument lists
    idents = IDENT_RE.findall(candidate)
    if not idents:
        return None
    # skip pure prose link text such as "source" or "line 12"
    if not code and not re.search(r"[A-Z.()]", text):
        return None
    return idents[-1]


def check():
    errors = []
    nlinks = 0
    for md in md_files():
        if not os.path.exists(md):
            errors.append(f"{os.path.relpath(md, ROOT)}: file missing")
            continue
        with open(md, encoding="utf-8") as fh:
            lines = fh.read().splitlines()
        in_fence = False
        for lineno, line in enumerate(lines, 1):
            if line.lstrip().startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            where = f"{os.path.relpath(md, ROOT)}:{lineno}"

            for text, target in LINK_RE.findall(line):
                if re.match(r"^[a-z]+:", target) or target.startswith("#"):
                    continue
                nlinks += 1
                path, _, anchor = target.partition("#")
                full = os.path.normpath(os.path.join(os.path.dirname(md), path))
                if not os.path.exists(full):
                    errors.append(f"{where}: missing target {target}")
                    continue
                m = ANCHOR_RE.match(anchor) if anchor else None
                if not m or not os.path.isfile(full):
                    continue
                start = int(m.group(1))
                end = int(m.group(2) or start)
                with open(full, encoding="utf-8", errors="replace") as src:
                    src_lines = src.read().splitlines()
                if end > len(src_lines):
                    errors.append(f"{where}: {target} beyond end of file ({len(src_lines)} lines)")
                    continue
                sym = symbol_from_text(text)
                if sym:
                    lo, hi = max(0, start - 1 - SLACK), min(len(src_lines), end + SLACK)
                    window = "\n".join(src_lines[lo:hi])
                    if not re.search(r"\b" + re.escape(sym) + r"\b", window):
                        errors.append(f"{where}: '{sym}' not found near {target} (anchor drifted?)")

            for fqcn in FQCN_RE.findall(line):
                suffix = fqcn.replace(".", "/") + ".java"
                if not any(p.endswith(suffix) for p in java_index()):
                    errors.append(f"{where}: class {fqcn} not found")

    for e in errors:
        print("BROKEN  " + e)
    print(f"checked {nlinks} links; {len(errors)} broken")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(check())
