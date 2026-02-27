"""GitHub PR Manager for AI code reviews and automated commits.

Uses the GitHub API via the `PyGithub` library. Requires a Personal
Access Token (PAT) with repository scopes.
"""

from __future__ import annotations

import logging
from typing import Dict, Optional, Tuple

from modules.dev_team import run_reviewer_phase

logger = logging.getLogger(__name__)


def _ensure_github_deps() -> str | None:
    """Auto-install PyGithub if missing."""
    from modules.dependency_manager import ensure_packages
    ok, msg = ensure_packages("GitHub PR Manager", extra_packages=[("PyGithub", "github")])
    return None if ok else msg


def analyze_pull_request(repo_name: str, pr_number: int, token: str) -> Tuple[str, Dict]:
    """Fetch a PR's diff and run it through the Dev Team Reviewer agent.
    
    Returns (status_message, pr_data).
    """
    err = _ensure_github_deps()
    if err:
        return err, {}

    try:
        from github import Github, Auth
        from github.GithubException import GithubException
    except ImportError:
        return "❌ Failed to import PyGithub after installation attempt.", {}

    if not token or not token.strip():
        return "❌ A GitHub Personal Access Token (PAT) is required.", {}

    auth = Auth.Token(token.strip())
    g = Github(auth=auth)

    try:
        repo = g.get_repo(repo_name)
        pr = repo.get_pull(int(pr_number))
        
        # Get the files changed in the PR
        files = pr.get_files()
        diff_text = f"PR Title: {pr.title}\nDescription: {pr.body}\n\n--- CHANGES ---\n"
        
        file_count = 0
        for f in files:
            file_count += 1
            if file_count > 15:
                diff_text += f"\n...and {files.totalCount - 15} more files omitted for brevity.\n"
                break
            diff_text += f"\nFile: {f.filename} ({f.status})\n"
            if f.patch:
                diff_text += f"```diff\n{f.patch}\n```\n"

        # Ask the Reviewer agent to critique the patch
        # The reviewer expects (code, blueprint). We'll pass the diff as the code
        # and a generated prompt as the blueprint.
        blueprint_prompt = (
            "Review this Pull Request diff. Look for security flaws, inefficient algorithms, "
            "missing tests, and stylistic issues. Provide actionable feedback."
        )
        
        critique, ai_err = run_reviewer_phase(diff_text, blueprint_prompt)
        if ai_err:
            return f"❌ AI Review failed: {ai_err}", {}

        data = {
            "title": pr.title,
            "author": pr.user.login,
            "diff_summary": f"{pr.additions} additions, {pr.deletions} deletions across {files.totalCount} files.",
            "critique": critique
        }
        
        return f"✅ Analyzed PR #{pr_number}.", data

    except GithubException as e:
        return f"❌ GitHub API Error: {e.data.get('message', str(e))}", {}
    except Exception as e:
        return f"❌ Unexpected Error: {e}", {}


def create_ai_pull_request(
    repo_name: str, 
    base_branch: str, 
    new_branch_name: str, 
    commit_message: str, 
    pr_title: str, 
    pr_body: str, 
    files_to_update: Dict[str, str], # Dict mapping filepath -> new_content
    token: str
) -> Tuple[str, Optional[str]]:
    """Automatically commits code changes and opens a PR using the GitHub API."""
    err = _ensure_github_deps()
    if err:
        return err, None

    try:
        from github import Github, Auth, InputGitTreeElement
        from github.GithubException import GithubException
    except ImportError:
        return "❌ Failed to import PyGithub after installation attempt.", None

    if not token or not token.strip():
        return "❌ A GitHub Personal Access Token is required to create PRs.", None

    auth = Auth.Token(token.strip())
    g = Github(auth=auth)

    try:
        repo = g.get_repo(repo_name)
        
        # 1. Get the SHA of the base branch
        base_ref = repo.get_git_ref(f"heads/{base_branch}")
        base_commit = repo.get_git_commit(base_ref.object.sha)
        base_tree = repo.get_git_tree(base_commit.tree.sha)

        # 2. Create the new branch reference
        try:
            repo.create_git_ref(ref=f"refs/heads/{new_branch_name}", sha=base_commit.sha)
        except GithubException as e:
            if e.status == 422: # Reference already exists
                return f"❌ Branch '{new_branch_name}' already exists on remote.", None
            raise e

        # 3. Create a tree with the new files
        tree_elements = []
        for filepath, content in files_to_update.items():
            element = InputGitTreeElement(
                path=filepath,
                mode='100644',
                type='blob',
                content=content
            )
            tree_elements.append(element)
            
        new_tree = repo.create_git_tree(tree_elements, base_tree)

        # 4. Create the commit
        new_commit = repo.create_git_commit(
            message=commit_message,
            tree=new_tree,
            parents=[base_commit]
        )

        # 5. Update the new branch ref to the new commit
        new_ref = repo.get_git_ref(f"heads/{new_branch_name}")
        new_ref.edit(sha=new_commit.sha)

        # 6. Open the PR
        pr = repo.create_pull(
            title=pr_title,
            body=pr_body,
            head=new_branch_name,
            base=base_branch
        )

        return f"✅ Pull Request successfully created!", pr.html_url

    except GithubException as e:
        return f"❌ GitHub API Error: {e.data.get('message', str(e))}", None
    except Exception as e:
        return f"❌ Unexpected Error: {e}", None
