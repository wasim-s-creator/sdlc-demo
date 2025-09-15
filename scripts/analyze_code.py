import subprocess
import os
from pathlib import Path

branch = os.environ.get("GITHUB_REF", "").replace("refs/heads/", "")
sha = (os.environ.get("GITHUB_SHA") or "")[:7]

# Prepare output folder
output_dir = Path("outputs")
output_dir.mkdir(exist_ok=True)
out_path = output_dir / f"analysis_{branch}_{sha}.md"

def run(cmd):
    """Run a shell command and return output"""
    result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    return result.stdout.strip()

def highlight_output(tool_name, output):
    """Format output with colors"""
    if not output:
        return f"## {tool_name}\n- ✅ No issues found\n\n"

    lines = output.splitlines()
    errors, fixes = [], []

    for line in lines:
        # crude separation — errors vs suggestions
        if "error" in line.lower() or "E:" in line:
            errors.append(f"<span style='color:red'>{line}</span>")
        elif "warning" in line.lower() or "W:" in line or "suggestion" in line.lower():
            fixes.append(f"<span style='color:green'>{line}</span>")
        else:
            errors.append(f"<span style='color:red'>{line}</span>")  # default treat as error

    report = [f"## {tool_name}\n"]
    if errors:
        report.append("### Errors")
        report.extend([f"- {e}" for e in errors])
    if fixes:
        report.append("\n### Suggestions & Fixes")
        report.extend([f"- {f}" for f in fixes])

    return "\n".join(report) + "\n\n", fixes

summary = f"# Code Analysis Report — {branch} @ {sha}\n\n"
all_fixes = []

# Run checks
flake8_out = run("flake8 . || true")
section, fixes = highlight_output("Flake8 Linting", flake8_out)
summary += section
all_fixes.extend(fixes)

pylint_out = run("pylint **/*.py || true")
section, fixes = highlight_output("Pylint Report", pylint_out)
summary += section
all_fixes.extend(fixes)

mypy_out = run("mypy . || true")
section, fixes = highlight_output("Type Checking (mypy)", mypy_out)
summary += section
all_fixes.extend(fixes)

black_out = run("black --check . || true")
section, fixes = highlight_output("Formatting suggestions", black_out)
summary += section
all_fixes.extend(fixes)

isort_out = run("isort --check-only . || true")
section, fixes = highlight_output("Import sorting check", isort_out)
summary += section
all_fixes.extend(fixes)

# Consolidated updates
if all_fixes:
    summary += "---\n## Consolidated Updates (Quick Reference)\n"
    for fix in all_fixes:
        summary += f"- {fix}\n"
else:
    summary += "---\n## Consolidated Updates (Quick Reference)\n- No fixes required 🎉\n"

out_path.write_text(summary)
print(f"✅ Analysis written to {out_path}")
