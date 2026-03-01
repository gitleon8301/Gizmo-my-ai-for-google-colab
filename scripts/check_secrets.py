#!/usr/bin/env python3
"""
scripts/check_secrets.py — Scan for accidentally committed secrets.

Checks for patterns matching:
  - Google OAuth client IDs/secrets
  - OpenAI API keys
  - HuggingFace tokens
  - GitHub personal access tokens
  - Generic high-entropy strings that look like secrets

Usage:
    python scripts/check_secrets.py [path]
    python scripts/check_secrets.py --install-hook   # installs as pre-commit hook
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Secret patterns
# ---------------------------------------------------------------------------

PATTERNS = [
    ("Google OAuth Client ID",     re.compile(r"\d{12}-[a-zA-Z0-9]{32}\.apps\.googleusercontent\.com")),
    ("Google OAuth Client Secret", re.compile(r"GOCSPX-[a-zA-Z0-9_\-]{28}")),
    ("OpenAI API Key",             re.compile(r"sk-[a-zA-Z0-9]{48}")),
    ("OpenAI Org ID",              re.compile(r"org-[a-zA-Z0-9]{24}")),
    ("HuggingFace Token",          re.compile(r"hf_[a-zA-Z0-9]{34}")),
    ("GitHub PAT (classic)",       re.compile(r"ghp_[a-zA-Z0-9]{36}")),
    ("GitHub PAT (fine-grained)",  re.compile(r"github_pat_[a-zA-Z0-9_]{82}")),
    ("AWS Access Key",             re.compile(r"AKIA[A-Z0-9]{16}")),
    ("Generic secret env var",     re.compile(r'(?:SECRET|PASSWORD|API_KEY|TOKEN)\s*=\s*["\'](?!<|your|change)[a-zA-Z0-9+/=_\-]{16,}["\']', re.IGNORECASE)),
]

# Files and directories to skip
SKIP_DIRS  = {".git", "node_modules", "__pycache__", ".venv", "venv", ".mypy_cache"}
SKIP_FILES = {"package-lock.json", "yarn.lock"}
SKIP_EXTS  = {".pyc", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".woff", ".ttf", ".db"}

# Files that are explicitly allowed to contain these patterns (e.g., docs, templates)
ALLOWLIST_FILES = {"google_oauth.env.template", "check_secrets.py", "DOMAIN_SETUP.md"}


# ---------------------------------------------------------------------------
# Scanner
# ---------------------------------------------------------------------------

def scan_file(path: Path) -> list[tuple[str, int, str, str]]:
    """
    Scan *path* for secret patterns.

    Returns list of (pattern_name, line_number, matched_text, file_path).
    """
    if path.name in ALLOWLIST_FILES:
        return []
    if path.suffix.lower() in SKIP_EXTS:
        return []

    findings = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []

    for line_no, line in enumerate(text.splitlines(), 1):
        for name, pattern in PATTERNS:
            match = pattern.search(line)
            if match:
                findings.append((name, line_no, match.group(), str(path)))

    return findings


def scan_directory(root: Path) -> list[tuple[str, int, str, str]]:
    all_findings = []
    for p in root.rglob("*"):
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.name in SKIP_FILES:
            continue
        if p.is_file():
            all_findings.extend(scan_file(p))
    return all_findings


# ---------------------------------------------------------------------------
# Pre-commit hook installer
# ---------------------------------------------------------------------------

def install_hook(repo_root: Path) -> None:
    hook_path = repo_root / ".git" / "hooks" / "pre-commit"
    script = (
        "#!/bin/sh\n"
        "python3 scripts/check_secrets.py . || exit 1\n"
    )
    hook_path.write_text(script, encoding="utf-8")
    hook_path.chmod(0o755)
    print(f"✅ Pre-commit hook installed at {hook_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Scan for accidentally committed secrets.")
    parser.add_argument("path", nargs="?", default=".", help="Directory to scan")
    parser.add_argument("--install-hook", action="store_true", help="Install as git pre-commit hook")
    args = parser.parse_args()

    root = Path(args.path).resolve()

    if args.install_hook:
        install_hook(root)
        return 0

    print(f"🔍 Scanning {root} …")
    findings = scan_directory(root)

    if not findings:
        print("✅ No secrets found.")
        return 0

    print(f"\n⚠️  Found {len(findings)} potential secret(s):\n")
    for name, line_no, matched, filepath in findings:
        # Redact the matched value in output
        redacted = matched[:6] + "…" + matched[-3:] if len(matched) > 12 else "***"
        print(f"  [{name}] {filepath}:{line_no}  →  {redacted}")

    print(
        "\n🛑 Commit blocked. Please remove or gitignore the above secrets.\n"
        "   If this is a false positive, add the file name to ALLOWLIST_FILES in\n"
        "   scripts/check_secrets.py"
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
