"""Intelligent Auto-Debugger and Traceback Analyzer.

Parses Python tracebacks to extract the exact file and line number where
a crash occurred, retrieves that code via AST or direct file reading, and
asks the Dev Team `Coder` agent to generate a unified diff to fix it.
"""

from __future__ import annotations

import os
import re
from typing import Dict, List, Optional, Tuple

from modules.dev_team import call_ai


# ------------------------------------------------------------------
# Traceback Parsing
# ------------------------------------------------------------------

def parse_traceback(tb_text: str) -> List[Dict[str, str]]:
    """Extracts File, Line, and Function/Module info from a raw traceback."""
    frames = []
    # Match standard Python traceback lines:
    # File "/path/to/file.py", line 42, in function_name
    pattern = re.compile(r'File "(.*?)", line (\d+), in (.*)')
    
    for line in tb_text.splitlines():
        match = pattern.search(line)
        if match:
            filepath, lineno, func_name = match.groups()
            frames.append({
                "filepath": filepath,
                "line": lineno,
                "function": func_name
            })
    return frames


def get_local_source_for_frame(filepath: str, center_line: int, window: int = 15) -> str:
    """Read `window` lines around the crash site from the local file."""
    if not os.path.exists(filepath):
        return f"# File not found locally: {filepath}"
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        return f"# Error reading file {filepath}: {e}"

    start_idx = max(0, center_line - window - 1)
    end_idx = min(len(lines), center_line + window)
    
    context = []
    for i in range(start_idx, end_idx):
        prefix = "> " if i + 1 == center_line else "  "
        context.append(f"{i + 1:4d} {prefix}{lines[i].rstrip()}")
        
    return "\n".join(context)


# ------------------------------------------------------------------
# LLM Patch Generation
# ------------------------------------------------------------------

DEBUGGER_PROMPT = (
    "You are an Expert Python Debugger. A system has crashed with a Traceback. "
    "I will provide the traceback, the error message, and the exact lines of "
    "source code where the crash occurred.\n\n"
    "Your job is to:\n"
    "1. Briefly explain the root cause of the error.\n"
    "2. Provide the corrected block of code to replace the broken one.\n\n"
    "Do NOT rewrite the entire file. Show only the specific function/block that needs to change."
)

def analyze_and_fix(traceback_text: str) -> Tuple[str, Optional[str]]:
    """Full workflow: Parse TB -> Get Context -> Ask LLM -> Return Solution."""
    frames = parse_traceback(traceback_text)
    
    if not frames:
        return call_ai(
            f"{DEBUGGER_PROMPT}\n\n"
            f"--- TRACEBACK (Unrecognized Format) ---\n{traceback_text}\n\n"
            "Please try to diagnose based purely on the error message provided."
        )

    # Usually the last frame is where the crash originated locally
    # Find the deepest frame that looks local (not in Python's standard library or site-packages)
    local_frame = frames[-1]
    for frame in reversed(frames):
        if "site-packages" not in frame["filepath"] and "lib/python" not in frame["filepath"].lower():
            local_frame = frame
            break

    filepath = local_frame["filepath"]
    lineno = int(local_frame["line"])
    
    source_context = get_local_source_for_frame(filepath, lineno)

    prompt = (
        f"{DEBUGGER_PROMPT}\n\n"
        f"--- FULL TRACEBACK ---\n{traceback_text}\n\n"
        f"--- CRASH CONTEXT ({os.path.basename(filepath)} at line {lineno}) ---\n"
        f"{source_context}\n"
    )

    return call_ai(prompt)
