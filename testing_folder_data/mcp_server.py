# --- File: mcp_server.py (Branch Support Version) ---
import os
import requests
import json
import base64 
import sys 
from fastmcp import FastMCP, Context
import traceback
from typing import List, Dict, Any
from github import Github, GithubException, Auth

# --- Initialize the MCP Server ---
mcp = FastMCP("githubexpertj6jan")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

def _get_github_client():
    """Lazy initialization of the GitHub client."""
    if not GITHUB_TOKEN:
        return None
    try:
        auth = Auth.Token(GITHUB_TOKEN)
        client = Github(auth=auth)
        client.get_rate_limit()
        return client
    except Exception as e:
        print(f"ERROR: GitHub Client initialization failed: {e}", file=sys.stderr)
        return None

def _get_auth_headers():
    """Utility to ensure headers are created consistently for all requests calls."""
    if not GITHUB_TOKEN:
        raise ValueError("GITHUB_TOKEN environment variable is missing.")
    return {
        "Authorization": f"token {GITHUB_TOKEN}", 
        "Accept": "application/vnd.github.v3+json"
    }

# UPDATED: Added 'ref' parameter to support branches
def _get_contents(owner: str, repo: str, path: str = "", ref: str = None):
    """Standard Python function to fetch repo contents."""
    try:
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
        params = {"ref": ref} if ref else {}
        response = requests.get(url, headers=_get_auth_headers(), params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return f"ERROR: Failed to fetch contents: {str(e)}"

# UPDATED: Added 'ref' parameter
def _list_contents_logic(owner: str, repo: str, path: str = "", ref: str = None):
    """Standard function that actually performs the API request."""
    try:
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
        params = {"ref": ref} if ref else {}
        response = requests.get(url, headers=_get_auth_headers(), params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return f"ERROR: {e}"

@mcp.tool()
def list_branches(owner: str, repo: str) -> str:
    """Lists all branches in the repository."""
    url = f"https://api.github.com/repos/{owner}/{repo}/branches"
    try:
        response = requests.get(url, headers=_get_auth_headers())
        response.raise_for_status()
        branches = [b['name'] for b in response.json()]
        return json.dumps({"branches": branches})
    except Exception as e:
        return f"ERROR: Failed to list branches: {e}"

# UPDATED: Added 'ref' support
@mcp.tool()
def list_repo_contents(owner: str, repo: str, path: str = "", ref: str = None) -> str:
    """Lists files and folders at a path. Provide 'ref' for specific branches."""
    data = _list_contents_logic(owner, repo, path, ref=ref)
    if isinstance(data, str): return data 
    return json.dumps(data)
def _read_file_logic(owner: str, repo: str, path: str, ref: str = None) -> str:
    """The actual logic to read a file."""
    try:
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
        headers = _get_auth_headers()
        headers["Accept"] = "application/vnd.github.v3.raw" 
        params = {"ref": ref} if ref else {}
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.text 
    except Exception as e: 
        return f"ERROR: {e}"
@mcp.tool()
def read_file_content(owner: str, repo: str, path: str, ref: str = None) -> str:
    """Tool wrapper for reading file content."""
    return _read_file_logic(owner, repo, path, ref)

# @mcp.tool()
# def read_file_content(owner: str, repo: str, path: str, ref: str = None) -> str:
#     """Retrieves raw content of a file. Provide 'ref' for specific branches."""
#     try:
#         url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
#         headers = _get_auth_headers()
#         headers["Accept"] = "application/vnd.github.v3.raw" 
#         params = {"ref": ref} if ref else {}
        
#         response = requests.get(url, headers=headers, params=params)
#         response.raise_for_status()
#         return response.text 
#     except Exception as e: 
#         return f"ERROR: Failed to read file content: {e}"

@mcp.tool()
def get_project_dependencies(owner: str, repo: str, path: str = "requirements.txt", ref: str = None) -> str:
    """Retrieves dependency file content. Provide 'ref' for specific branches."""
    try:
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
        headers = _get_auth_headers()
        headers["Accept"] = "application/vnd.github.v3.raw" 
        params = {"ref": ref} if ref else {}
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.text
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return f"INFO: Dependency file '{path}' not found."
        return f"ERROR: {e}"
    except Exception as e:
        return f"ERROR: {e}"

@mcp.tool()
def get_github_repo_info(owner: str, repo: str) -> str:
    """Retrieves metadata like stars and issues for the repository."""
    try:
        url = f"https://api.github.com/repos/{owner}/{repo}"
        response = requests.get(url, headers=_get_auth_headers())
        response.raise_for_status()
        data = response.json()
        info = {
            "name": data.get("full_name"),
            "stars": data.get("stargazers_count"), 
            "open_issues": data.get("open_issues_count"),
            "language": data.get("language"),
            "description": data.get("description")
        }
        return json.dumps(info, indent=2)
    except Exception as e: 
        return f"ERROR: Failed to get repo info: {e}"

# UPDATED: Now uses 'ref' for the contents check
@mcp.tool()
def analyze_and_suggest_readme(owner: str, repo: str, path: str = "", ref: str = None) -> str:
    """Checks for a README at a path. Use 'ref' for specific branches."""
    contents = _get_contents(owner, repo, path, ref=ref)
    
    if isinstance(contents, str) and contents.startswith("ERROR"):
        return contents
    
    try:
        readme_item = next((item for item in contents if item.get("name", "").lower().startswith("readme")), None)
        readme_name = readme_item.get("name", "") if readme_item else ""
        root_files_context = [
            {"name": item.get("name"), "type": item.get("type"), "size": item.get("size", 0)}
            for item in contents if item.get("type") in ["file", "dir"] and item.get("name") != readme_name
        ]

        if readme_item:
            file_path = os.path.join(path, readme_item.get("name")).replace('\\', '/')
            existing_content = _read_file_logic(owner, repo, file_path, ref=ref)
            
            return json.dumps({
                "status": "README_EXISTS_NEEDS_ANALYSIS",
                "existing_readme_content": existing_content,
                "root_files_context": root_files_context
            }, indent=2)
        else:
            return json.dumps({
                "status": "NO_README_FOUND",
                "root_files_context": root_files_context,
                "suggestion_needed": "true"
            }, indent=2)
    except Exception as e:
        return f"ERROR: {e}"

@mcp.tool()
def list_repo_directories(owner: str, repo: str, path: str = "", ref: str = None) -> str:
    """
    Lists only the subdirectories within a specific path of the repository.
    Use this to give the user a choice of which folders to scan.
    """
    contents = _get_contents(owner, repo, path, ref=ref)
    
    if isinstance(contents, str) and contents.startswith("ERROR"):
        return contents
    
    try:
        # Filter for only items that are directories
        directories = [item['name'] for item in contents if item.get("type") == "dir"]
        return json.dumps({
            "parent_path": path or "root",
            "subdirectories": directories
        }, indent=2)
    except Exception as e:
        return f"ERROR: Failed to list directories: {e}"

@mcp.tool()
def find_readme_targets(owner: str, repo: str, base_path: str = "", include_paths: list = None, ref: str = None) -> str:
    """
    Scans for subdirectories missing READMEs. 
    If 'include_paths' is provided (list of folder names), only those folders are scanned.
    Otherwise, scans all subdirectories in 'base_path'.
    """
    # 1. Determine which directories to scan
    if include_paths:
        # User selected specific folders
        dirs_to_scan = [{"name": p} for p in include_paths]
    else:
        # Full scan: get all directories from base_path
        contents = _get_contents(owner, repo, base_path, ref=ref)
        if isinstance(contents, str) and contents.startswith("ERROR"):
            return contents
        dirs_to_scan = [item for item in contents if item.get("type") == "dir"]

    try:
        targets = []
        scanned_paths = []
        
        for subdir in dirs_to_scan:
            # Construct the proper path
            subdir_path = os.path.join(base_path, subdir['name']).replace('\\', '/')
            scanned_paths.append(subdir_path)
            
            # Fetch contents of this specific subdirectory
            subdir_contents = _get_contents(owner, repo, subdir_path, ref=ref)
            
            if isinstance(subdir_contents, str) and subdir_contents.startswith("ERROR"):
                continue 
            
            # Check for README and code presence
            has_readme = any(item.get("name", "").lower().startswith("readme") for item in subdir_contents)
            has_code_files = any(item.get("type") == "file" for item in subdir_contents)
            
            if has_code_files and not has_readme:
                targets.append(subdir_path)

        return json.dumps({
            "status": "SCAN_COMPLETE",
            "mode": "TARGETED" if include_paths else "FULL",
            "targets_identified": targets,
            "paths_checked": scanned_paths
        }, indent=2)
    except Exception as e:
        return f"ERROR: {e}"

@mcp.tool()
def create_branch(owner: str, repo: str, new_branch: str, source_branch: str = "main") -> str:
    """Creates a new branch from a source branch."""
    headers = _get_auth_headers()
    ref_url = f"https://api.github.com/repos/{owner}/{repo}/git/ref/heads/{source_branch}"
    try:
        res = requests.get(ref_url, headers=headers)
        res.raise_for_status()
        sha = res.json()["object"]["sha"]
        
        create_url = f"https://api.github.com/repos/{owner}/{repo}/git/refs"
        payload = {"ref": f"refs/heads/{new_branch}", "sha": sha}
        post_res = requests.post(create_url, headers=headers, json=payload)
        post_res.raise_for_status()
        return f"SUCCESS: Branch '{new_branch}' created from '{source_branch}'."
    except Exception as e:
        return f"ERROR: Failed to create branch: {e}"

@mcp.tool()
def commit_file_to_github(owner: str, repo: str, path: str, content: str, branch: str, commit_message: str = "docs: add auto-generated README") -> str:
    """Commits a file to a specific branch."""
    headers = _get_auth_headers()
    clean_path = path.strip("/")
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{clean_path}"
    
    sha = None
    check_res = requests.get(url, headers=headers, params={"ref": branch})
    if check_res.status_code == 200:
        sha = check_res.json().get("sha")

    encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
    payload = {
        "message": commit_message,
        "content": encoded_content,
        "branch": branch
    }
    if sha:
        payload["sha"] = sha

    try:
        response = requests.put(url, headers=headers, json=payload)
        response.raise_for_status()
        return f"SUCCESS: Committed to {branch}."
    except Exception as e:
        return f"ERROR: Commit failed: {e}"

@mcp.tool()
def create_pull_request(owner: str, repo: str, title: str, head_branch: str, base_branch: str = "main", body: str = "Pull Request created by an ADK agent.") -> str:
    """Creates a pull request from head_branch into base_branch."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    headers = _get_auth_headers()
    payload = {"title": title, "head": head_branch, "base": base_branch, "body": body}
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        pr_info = response.json()
        return json.dumps({
            "status": "PR_CREATED", 
            "number": pr_info.get("number"), 
            "html_url": pr_info.get("html_url"), 
            "message": f"Successfully created PR #{pr_info.get('number')}."
        })
    except Exception as e: return f"ERROR: Failed to create PR: {e}"

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    try:
        print(f"Starting MCP SSE Server on port {port}...")
        mcp.run(transport='sse', host='0.0.0.0', port=port)
    except Exception as e:
        print("--- UNCAUGHT MCP SERVER CRASH REPORT ---", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
