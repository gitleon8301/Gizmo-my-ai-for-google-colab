"""The Multi-Agent Dev Team module.

Coordinates multiple AI agents (Architect, Coder, Reviewer) to perform
Chain-of-Thought planning and code generation. Relies on `modules.ai_helper`
for actual LLM calls.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple
from modules.ai_helper import call_ai


# ------------------------------------------------------------------
# Agent System Prompts
# ------------------------------------------------------------------

ARCHITECT_PROMPT = (
    "You are the Lead Software Architect. Your job is to create a 'Chain of Thought' blueprint "
    "before any code is written.\n\n"
    "Given the user request and codebase context, explicitly output:\n"
    "1. Requirements Understanding\n"
    "2. Edge Cases (Security, Performance)\n"
    "3. Proposed Architecture / Data Structures\n"
    "4. Step-by-Step Implementation Plan\n\n"
    "Do NOT write the actual implementation code. Write only the blueprint."
)

CODER_PROMPT = (
    "You are the Senior Software Engineer. Your job is to write clean, idiomatic, "
    "and robust code based strictly on the Architect's blueprint.\n\n"
    "You must output only the raw code with minimal explanation. Include docstrings "
    "and type hints. Ensure your code directly addresses the edge cases mentioned in the plan."
)

REVIEWER_PROMPT = (
    "You are the Principal Security & Code Reviewer. You are reviewing the Coder's implementation "
    "against the Architect's blueprint.\n\n"
    "You must aggressively look for:\n"
    "- Security vulnerabilities (injection, hardcoded secrets)\n"
    "- Architecture smells (O(N^2) complexity, tight coupling)\n"
    "- Missed edge cases\n\n"
    "If the code is perfect, reply EXACTLY with 'APPROVED'. If there are issues, provide a "
    "formatted list of required changes and unified diffs showing how to fix them."
)


# ------------------------------------------------------------------
# Orchestration Pipeline
# ------------------------------------------------------------------

def run_architect_phase(user_query: str, context: str) -> Tuple[str, Optional[str]]:
    """Runs the Chain of Thought Architect agent."""
    prompt = (
        f"{ARCHITECT_PROMPT}\n\n"
        f"--- CONTEXT ---\n{context}\n\n"
        f"--- USER REQUEST ---\n{user_query}\n"
    )
    return call_ai(prompt)


def run_coder_phase(user_query: str, blueprint: str, context: str) -> Tuple[str, Optional[str]]:
    """Runs the Coder agent to implement the blueprint."""
    prompt = (
        f"{CODER_PROMPT}\n\n"
        f"--- CONTEXT ---\n{context}\n\n"
        f"--- ARCHITECT BLUEPRINT ---\n{blueprint}\n\n"
        f"--- USER REQUEST ---\n{user_query}\n"
    )
    return call_ai(prompt)


def run_reviewer_phase(code: str, blueprint: str) -> Tuple[str, Optional[str]]:
    """Runs the Critic/Reviewer agent to check the code."""
    prompt = (
        f"{REVIEWER_PROMPT}\n\n"
        f"--- ARCHITECT BLUEPRINT ---\n{blueprint}\n\n"
        f"--- CODER IMPLEMENTATION ---\n{code}\n"
    )
    return call_ai(prompt)


def full_dev_team_pipeline(user_query: str, context: str = "No context provided.") -> Dict[str, str]:
    """Execute the full 3-agent orchestration pipeline.
    
    Returns a dictionary of the logs/outputs from each stage.
    """
    results = {}

    # 1. Plan
    blueprint, err = run_architect_phase(user_query, context)
    if err:
        return {"error": f"Architect failed: {err}"}
    results["blueprint"] = blueprint

    # 2. Code
    code, err = run_coder_phase(user_query, blueprint, context)
    if err:
        return {"error": f"Coder failed: {err}", **results}
    results["code"] = code

    # 3. Review
    review, err = run_reviewer_phase(code, blueprint)
    if err:
        return {"error": f"Reviewer failed: {err}", **results}
    results["review"] = review

    # If the review didn't say APPROVED, we could theoretically hook this up to
    # an auto-fix loop in the future that re-prompts the coder. For now, we return
    # the critique to the user.
    return results
