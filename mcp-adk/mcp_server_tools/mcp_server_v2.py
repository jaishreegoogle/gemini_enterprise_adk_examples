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
mcp = FastMCP("githubexpertj8jan")

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
    Lists subdirectories and explicitly includes the Root (.) as an option.
    """
    contents = _get_contents(owner, repo, path, ref=ref)
    
    if isinstance(contents, str) and contents.startswith("ERROR"):
        return contents
    
    try:
        # Get actual folders
        directories = [item['name'] for item in contents if item.get("type") == "dir"]
        
        # If we are at the root level, prepend the Root (.) option
        display_list = directories
        if path == "" or path == ".":
            display_list = ["Root (.)"] + directories

        return json.dumps({
            "parent_path": path or "root",
            "available_targets": display_list
        }, indent=2)
    except Exception as e:
        return f"ERROR: {e}"

@mcp.tool()
def find_readme_targets(owner: str, repo: str, base_path: str = "", include_paths: list = None, ref: str = None) -> str:
    """
    Scans for missing READMEs. Handles '.' as a request to scan the root.
    """
    targets = []
    
    # 1. If include_paths is provided, check if Root is requested
    if include_paths:
        if "." in include_paths or "Root (.)" in include_paths:
            root_contents = _get_contents(owner, repo, "", ref=ref)
            has_root_readme = any(i.get("name", "").lower().startswith("readme") for i in root_contents)
            if not has_root_readme:
                targets.append(".")
        
        # Then check the specific subdirectories requested
        dirs_to_check = [p for p in include_paths if p not in [".", "Root (.)"]]
    else:
        # Default full scan logic
        contents = _get_contents(owner, repo, base_path, ref=ref)
        dirs_to_check = [item['name'] for item in contents if item.get("type") == "dir"]

    # 2. Scan the subdirectories
    for subdir in dirs_to_check:
        path = f"{base_path}/{subdir}".strip("/")
        subdir_contents = _get_contents(owner, repo, path, ref=ref)
        if isinstance(subdir_contents, str): continue
        
        has_readme = any(i.get("name", "").lower().startswith("readme") for i in subdir_contents)
        has_code = any(i.get("type") == "file" for i in subdir_contents)
        if has_code and not has_readme:
            targets.append(path)

    return json.dumps({"targets_identified": targets})

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

# @mcp.tool()
# def commit_file_to_github(owner: str, repo: str, path: str, content: str, branch: str, commit_message: str = "docs: add auto-generated README") -> str:
#     """Commits a file to a specific branch."""
#     headers = _get_auth_headers()
#     clean_path = path.strip("/")
#     url = f"https://api.github.com/repos/{owner}/{repo}/contents/{clean_path}"
    
#     sha = None
#     check_res = requests.get(url, headers=headers, params={"ref": branch})
#     if check_res.status_code == 200:
#         sha = check_res.json().get("sha")

#     encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
#     payload = {
#         "message": commit_message,
#         "content": encoded_content,
#         "branch": branch
#     }
#     if sha:
#         payload["sha"] = sha

#     try:
#         response = requests.put(url, headers=headers, json=payload)
#         response.raise_for_status()
#         return f"SUCCESS: Committed to {branch}."
#     except Exception as e:
#         return f"ERROR: Commit failed: {e}"
@mcp.tool()
def commit_file_to_github(owner: str, repo: str, path: str, content: str, branch: str, commit_message: str = "docs: update repository documentation") -> str:
    """
    Commits a file to a specific branch. 
    Smart path handling to prevent README.md/README.md errors.
    """
    headers = _get_auth_headers()
    
    # 1. SMART PATH NORMALIZATION
    clean_path = path.strip("/")
    
    # If path is root markers, target is top-level README
    if clean_path in [".", "", "Root (.)"]:
        target_path = "README.md"
    # If the agent already included 'README.md' in the path, don't double it
    elif clean_path.lower().endswith("readme.md"):
        target_path = clean_path
    # Otherwise, assume it's a directory and append README.md
    else:
        target_path = f"{clean_path}/README.md"

    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{target_path}"
    
    # 2. Check for existing file SHA on the SPECIFIC branch
    sha = None
    try:
        check_res = requests.get(url, headers=headers, params={"ref": branch})
        if check_res.status_code == 200:
            sha = check_res.json().get("sha")
    except:
        pass 

    # 3. Payload Preparation
    encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
    payload = {
        "message": commit_message,
        "content": encoded_content,
        "branch": branch
    }
    if sha:
        payload["sha"] = sha

    # 4. Execute
    try:
        response = requests.put(url, headers=headers, json=payload)
        response.raise_for_status()
        return f"SUCCESS: Committed to {target_path} on branch {branch}."
    except Exception as e:
        return f"ERROR: Commit failed for {target_path}: {response.text if 'response' in locals() else str(e)}"

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
