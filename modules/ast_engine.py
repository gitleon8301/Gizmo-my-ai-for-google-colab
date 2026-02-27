"""AST-Aware Context Engine for semantic codebase search.

This module parses local Python files into an Abstract Syntax Tree (AST)
to index classes, methods, and functions. It allows the AI to request
semantic context (e.g. "Get me the implementation of user login") without
needing to load entire files into the context window.
"""

from __future__ import annotations

import ast
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class CodeNode:
    """Represents a parsed semantic block (class or function)."""
    def __init__(self, name: str, node_type: str, filepath: str, start_line: int, end_line: int, code: str, docstring: str = ""):
        self.name = name
        self.node_type = node_type  # "class" or "function"
        self.filepath = filepath
        self.start_line = start_line
        self.end_line = end_line
        self.code = code
        self.docstring = docstring

    def __repr__(self):
        return f"<{self.node_type.capitalize()} '{self.name}' in {os.path.basename(self.filepath)}>"


def _extract_source_segment(source_lines: List[str], node: ast.AST) -> str:
    """Extract the exact source code for an AST node safely."""
    start = node.lineno - 1
    end = getattr(node, "end_lineno", node.lineno)
    return "\n".join(source_lines[start:end])


def parse_python_file(filepath: str) -> List[CodeNode]:
    """Parse a single Python file into semantic CodeNodes."""
    nodes = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
        
        source_lines = source.splitlines()
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                docstring = ast.get_docstring(node) or ""
                code_segment = _extract_source_segment(source_lines, node)
                nodes.append(CodeNode(
                    name=node.name,
                    node_type="class",
                    filepath=filepath,
                    start_line=node.lineno,
                    end_line=getattr(node, "end_lineno", node.lineno),
                    code=code_segment,
                    docstring=docstring
                ))
            
            elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                docstring = ast.get_docstring(node) or ""
                code_segment = _extract_source_segment(source_lines, node)
                nodes.append(CodeNode(
                    name=node.name,
                    node_type="function",
                    filepath=filepath,
                    start_line=node.lineno,
                    end_line=getattr(node, "end_lineno", node.lineno),
                    code=code_segment,
                    docstring=docstring
                ))

    except Exception as e:
        # Silently skip unparseable files (e.g., syntax errors)
        pass
    
    return nodes


def index_directory(directory: str) -> Dict[str, List[CodeNode]]:
    """Recursively index a directory and return a dict mapping module names to nodes."""
    index: Dict[str, List[CodeNode]] = {}
    dir_path = Path(directory)
    
    if not dir_path.exists() or not dir_path.is_dir():
        return index

    for root, dirs, files in os.walk(directory):
        # Ignore common hidden/build directories
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ["__pycache__", "venv", "node_modules", "dist", "build"]]
        
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                nodes = parse_python_file(filepath)
                if nodes:
                    # Use relative path as the conceptual module name
                    rel_path = os.path.relpath(filepath, directory)
                    index[rel_path] = nodes

    return index


def semantic_search(query: str, index: Dict[str, List[CodeNode]], max_results=5) -> List[CodeNode]:
    """Extremely basic keyword-based semantic search over the AST index.
    In a production system, this would use vector embeddings, but keyword matching
    on node names and docstrings works as a V1 fallback.
    """
    query = query.lower()
    results = []

    for rel_path, nodes in index.items():
        for node in nodes:
            score = 0
            if query in node.name.lower():
                score += 10
            if query in node.docstring.lower():
                score += 5
            if query in rel_path.lower():
                score += 2
            
            if score > 0:
                results.append((score, node))

    # Sort by score descending and return top matches
    results.sort(key=lambda x: x[0], reverse=True)
    return [node for score, node in results[:max_results]]


def build_context_string(nodes: List[CodeNode]) -> str:
    """Format the retrieved nodes into a prompt-friendly string."""
    if not nodes:
        return "No relevant context found."
    
    context_parts = []
    for node in nodes:
        context_parts.append(
            f"--- File: {os.path.basename(node.filepath)} (Lines {node.start_line}-{node.end_line}) ---\n"
            f"Type: {node.node_type.capitalize()}\n"
            f"Name: {node.name}\n"
            f"```python\n{node.code}\n```"
        )
    return "\n\n".join(context_parts)
