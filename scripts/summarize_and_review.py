#!/usr/bin/env python3
"""
summarize_and_review.py
- Creates a markdown summary of changes (files, diff stat, diffs)
- Generates a small English summary of added/removed/modified code
- Runs a lightweight automated "review" producing recommendations:
    * TODOs/FIXMEs present
    * Binary files changed
    * Large files added/modified
    * Likely missing tests (src changes without tests)
    * Lack of docstrings for added functions (best-effort)
    * Commit message heuristics
- Emits outputs/summary_<branch>_<sha>.md and .pdf

Env:
- BASE_BRANCH (optional, default origin/main)
- GITHUB_REF, GITHUB_SHA (in Actions)
"""

import subprocess, os, re, textwrap, shutil
from pathlib import Path
from datetime import datetime

# PDF generation via reportlab (pure-python)
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted
    from reportlab.lib.units import mm
except Exception as e:
    # if reportlab missing, we will try to fallback later (workflow should install it)
    reportlab = None

# Config
BASE_BRANCH = os.environ.get("BASE_BRANCH", "origin/main")
branch = os.environ.get("GITHUB_REF", "").replace("refs/heads/", "") or "unknown-branch"
sha = (os.environ.get("GITHUB_SHA") or "")[:7] or "unknown"

out_dir = Path("outputs")
out_dir.mkdir(exist_ok=True)
md_path = out_dir / f"summary_{branch}_{sha}.md"
pdf_path = out_dir / f"summary_{branch}_{sha}.pdf"

def run(cmd, cwd=None):
    """Run shell cmd and return stdout (text). Does not raise on non-zero."""
    completed = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return completed.returncode, completed.stdout or completed.stderr

def ensure_fetch_history():
    # Ensure we have at least 2 commits; fetch base branch if needed
    run("git fetch --no-tags --prune --depth=2 origin || true")
    run(f"git fetch origin {BASE_BRANCH.split('/')[-1]} --depth=1 || true")

def get_diff_stat_and_patch():
    # Try HEAD~1..HEAD first; if not available, fallback to show HEAD
    rc, stat = run("git diff --stat HEAD~1 HEAD || true")
    rc2, patch = run("git diff --unified=3 HEAD~1 HEAD || true")
    if not stat.strip():
        # fallback: show diff of HEAD (useful for first commit or shallow)
        rc3, stat = run("git show --stat --pretty=\"\" HEAD || true")
        rc4, patch = run("git show --unified=3 HEAD || true")
    return stat.strip(), patch

def detect_binary_files(patch_text):
    # git diff will show "Binary files ... differ"
    binaries = []
    for line in patch_text.splitlines():
        if "Binary files " in line and " differ" in line:
            binaries.append(line.strip())
    return binaries

def size_checks_for_files(changed_files):
    # return list of (path, size_bytes) for files > threshold
    heavy = []
    threshold = 500 * 1024  # 500 KB
    for p in changed_files:
        pth = Path(p)
        if pth.exists():
            try:
                sz = pth.stat().st_size
                if sz > threshold:
                    heavy.append((p, sz))
            except Exception:
                pass
    return heavy

def list_changed_files_from_stat(stat_text):
    # parse lines like: path | 3 ++-
    files = []
    for line in stat_text.splitlines():
        line = line.strip()
        if not line:
            continue
        # skip summary lines like '1 file changed, 3 insertions(+), 0 deletions(-)'
        if re.match(r'^\d+ file(s)? changed', line):
            continue
        parts = line.split("|")
        if len(parts) >= 1:
            files.append(parts[0].strip())
    return files

# Light grammar for English summaries (best-effort)
def english_summary_from_patch(patch_text):
    results = []
    added_funcs = []
    removed_funcs = []
    modified_files = set()
    todos = []
    for line in patch_text.splitlines():
        if line.startswith("+++ b/"):
            current_file = line.replace("+++ b/","").strip()
            modified_files.add(current_file)
        if line.startswith("+") and not line.startswith("+++"):
            code = line[1:].strip()
            # function definitions
            m = re.match(r"def\s+([A-Za-z_]\w*)\s*\(", code)
            if m:
                added_funcs.append(m.group(1))
            m2 = re.match(r"class\s+([A-Za-z_]\w*)\s*[:\(]", code)
            if m2:
                results.append(f"Introduced class `{m2.group(1)}` in `{current_file}`.")
            if "TODO" in code or "FIXME" in code:
                todos.append(code)
            if re.search(r"\bprint\s*\(", code):
                results.append(f"Added print/logging statement in `{current_file}`: `{code}`")
            # generic added line
            if re.search(r"=", code) and not code.startswith("#"):
                results.append(f"Added/changed assignment or expression in `{current_file}`: `{code[:120]}`")
        if line.startswith("-") and not line.startswith("---"):
            code = line[1:].strip()
            m = re.match(r"def\s+([A-Za-z_]\w*)\s*\(", code)
            if m:
                removed_funcs.append(m.group(1))
            if "TODO" in code or "FIXME" in code:
                todos.append(code)
    if added_funcs:
        for fn in set(added_funcs):
            results.append(f"Added function `{fn}()`.")
    if removed_funcs:
        for fn in set(removed_funcs):
            results.append(f"Removed function `{fn}()`.")
    # de-duplicate and return
    dedup = []
    for r in results:
        if r not in dedup:
            dedup.append(r)
    return dedup, todos, sorted(list(modified_files))

def simple_test_detection(changed_files):
    # heuristics: if src/ changed but tests/ not changed, flag
    src_changed = any(p.startswith("src/") or p.startswith("app/") or p.endswith(".py") for p in changed_files)
    test_changed = any(p.startswith("tests/") or p.startswith("test_") or "/tests/" in p for p in changed_files)
    return src_changed and not test_changed

def commit_message_hint():
    rc, msg = run("git log -1 --pretty=%B || true")
    return msg.strip()

def build_markdown_report(stat, patch, eng_summary, todos, binaries, heavy_files, changed_files, review_recs):
    now = datetime.utcnow().isoformat() + "Z"
    md = []
    md.append(f"# Code summary — `{branch}` @ `{sha}`")
    md.append(f"*Generated: {now}*")
    md.append("")
    if stat:
        md.append("## Changed files (stat)")
        md.append("```")
        md.append(stat.strip())
        md.append("```")
    else:
        md.append("_No file stat available._")
    md.append("")
    if eng_summary:
        md.append("## English Summary (automated)")
        for s in eng_summary:
            md.append(f"- {s}")
    else:
        md.append("## English Summary (automated)")
        md.append("_No clear high-level changes detected by heuristics._")
    md.append("")
    if todos:
        md.append("## TODO / FIXME found")
        for t in todos[:20]:
            md.append(f"- `{t.strip()}`")
        md.append("")
    if binaries:
        md.append("## Binary files changed (warning)")
        for b in binaries:
            md.append(f"- {b}")
        md.append("")
    if heavy_files:
        md.append("## Large file changes (>= 500 KB)")
        for p, sz in heavy_files:
            md.append(f"- `{p}` — {sz} bytes")
        md.append("")
    # Review recommendations
    md.append("## Review: Automated code & process recommendations")
    md.append("")
    if review_recs:
        for r in review_recs:
            md.append(f"- {r}")
    else:
        md.append("- No automatic recommendations generated.")
    md.append("")
    md.append("## Raw Diff")
    md.append("```diff")
    md.append(patch.strip())
    md.append("```")
    return "\n".join(md)

def build_review_recommendations(changed_files, patch, todos, binaries, heavy_files):
    recs = []
    # 1. TODOs
    if todos:
        recs.append("Resolve TODO/FIXME items before merging; they often indicate incomplete logic or edge cases.")
    # 2. binary files
    if binaries:
        recs.append("Binary files changed — ensure these are intended (e.g., models, images). Prefer storing large artifacts in releases or object storage.")
    # 3. heavy files
    if heavy_files:
        recs.append("Large file changes detected; consider storing large assets outside the repo (S3/GCS) and reference them instead.")
    # 4. tests
    if simple_test_detection(changed_files):
        recs.append("Code changes detected without test changes — add unit/integration tests focused on the modified modules.")
    # 5. commit message
    cm = commit_message_hint()
    if not cm or len(cm.splitlines()[0]) < 10:
        recs.append("Commit message is short or missing. Use descriptive commit messages: [TYPE] scope: short description (e.g., feat(auth): add token refresh).")
    # 6. docstrings
    # best-effort: if functions added but no triple-quote nearby, warn
    m_added_funcs = re.findall(r'^\+.*def\s+([A-Za-z_]\w*)\s*\(', patch, flags=re.MULTILINE)
    if m_added_funcs:
        recs.append("New functions added; ensure they include docstrings and are covered by unit tests.")
    # 7. security hint
    if re.search(r"password|secret|api_key|token", patch, flags=re.IGNORECASE):
        recs.append("Possible secrets detected in diff — ensure secrets are stored in secure secrets manager and not committed.")
    # 8. formatting / linting
    recs.append("Run automated linters/formatters (e.g., black/isort/flake8 for Python) and fail the CI on lint errors.")
    # 9. CI safety
    recs.append("For changes touching infra/CI/CD or dependencies, require at least one approving review and run full integration tests.")
    return recs

def dump_pdf_from_markdown(md_text, pdf_file):
    "Generate a simple PDF using reportlab. If reportlab not installed, write a fallback text file."
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted
        from reportlab.lib.units import mm
    except Exception as e:
        # fallback: write plain .txt (but we will still name .pdf — not ideal)
        pdf_file.write_text(md_text)
        return False

    doc = SimpleDocTemplate(str(pdf_file), pagesize=A4,
                            rightMargin=15*mm, leftMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)
    styles = getSampleStyleSheet()
    story = []
    for paragraph in md_text.split("\n\n"):
        # Keep code blocks as preformatted
        if paragraph.startswith("```") and paragraph.endswith("```"):
            inner = paragraph.strip("`")
            story.append(Preformatted(inner, styles['Code']))
            story.append(Spacer(1,6))
        else:
            # wrap long lines
            para = Paragraph(textwrap.escape(paragraph).replace("\n","<br/>"), styles["BodyText"])
            story.append(para)
            story.append(Spacer(1,6))
    doc.build(story)
    return True

def main():
    ensure_fetch_history()
    stat, patch = get_diff_stat_and_patch()
    binaries = detect_binary_files(patch)
    changed_files = list_changed_files_from_stat(stat) if stat else []
    heavy_files = size_checks_for_files(changed_files)
    eng_summary, todos, _ = english_summary_from_patch(patch)
    review_recs = build_review_recommendations(changed_files, patch, todos, binaries, heavy_files)
    md = build_markdown_report(stat, patch, eng_summary, todos, binaries, heavy_files, changed_files, review_recs)

    # write markdown
    md_path.write_text(md, encoding="utf8")
    # write PDF
    dump_pdf_from_markdown(md, pdf_path)

    print(f"Wrote summary: {md_path}")
    print(f"Wrote PDF   : {pdf_path}")

if __name__ == "__main__":
    main()
