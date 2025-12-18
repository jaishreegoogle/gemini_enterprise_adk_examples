# --- File: mcp_server.py (Final Version with Subfolder Support) ---
import os
import requests
import json
import base64 
import sys 

from mcp.server.fastmcp import FastMCP 

# --- Initialize the MCP Server ---
mcp = FastMCP("GitHubTools")

# --- UTILITY AND CORE INFO TOOLS ---

@mcp.tool()
def read_file_content(owner: str, repo: str, path: str) -> str:
    """
    Retrieves the raw content (text) of any file in the repository (e.g., README.md).
    Requires the GITHUB_TOKEN.
    """
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token: return "ERROR: GITHUB_TOKEN is not set..."
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    headers = {"Authorization": f"token {github_token}", "Accept": "application/vnd.github.v3.raw"}
    try:
        response = requests.get(url, headers=headers); response.raise_for_status()
        return response.text 
    except Exception as e: return f"ERROR: Failed to read file content: {e}"


@mcp.tool()
def get_project_dependencies(owner: str, repo: str, path: str = "requirements.txt") -> str:
    """
    Retrieves the raw content of a specific dependency file (path can include subfolders).
    """
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token: return "ERROR: GITHUB_TOKEN is not set..."
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    headers = {"Authorization": f"token {github_token}", "Accept": "application/vnd.github.v3.raw"}
    try:
        response = requests.get(url, headers=headers); response.raise_for_status()
        return response.text
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return f"INFO: Dependency file '{path}' not found."
        return f"ERROR: Failed to retrieve dependency file content: {e}"
    except Exception as e:
        return f"ERROR: An unexpected error occurred: {e}"


@mcp.tool()
def get_github_repo_info(owner: str, repo: str) -> str:
    """Retrieves the star count, open issues count, and primary language for a public GitHub repository."""
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token: return "ERROR: GITHUB_TOKEN is not set..."
    url = f"https://api.github.com/repos/{owner}/{repo}"
    headers = {"Authorization": f"token {github_token}", "Accept": "application/vnd.github.v3+json"}
    try:
        response = requests.get(url, headers=headers); response.raise_for_status()
        data = response.json()
        info = {"name": data.get("full_name"), "stars": data.get("stargazers_count"), 
                "open_issues": data.get("open_issues_count"), "language": data.get("language"), 
                "description": data.get("description")}
        return json.dumps(info, indent=2)
    except Exception as e: return f"ERROR: Failed to get repo info: {e}"


@mcp.tool()
def list_repo_contents(owner: str, repo: str, path: str = "") -> str:
    """Lists the files and folders (contents) at a specific path within a public GitHub repository."""
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token: return "ERROR: GITHUB_TOKEN is not set..."
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    headers = {"Authorization": f"token {github_token}", "Accept": "application/vnd.github.v3+json"}
    try:
        response = requests.get(url, headers=headers); response.raise_for_status()
        contents = response.json()
        file_list = [{"name": item.get("name"), "type": item.get("type"), "size": item.get("size", 0)} for item in contents]
        return json.dumps(file_list, indent=2)
    except Exception as e: return f"ERROR: Failed to list contents: {e}"


# --- README ANALYSIS TOOL (MODIFIED FOR PATHS) ---

@mcp.tool()
def analyze_and_suggest_readme(owner: str, repo: str, path: str = "") -> str:
    """
    Checks for a README.md in a specified path. If found, it reads the content and 
    returns it for the LLM to analyze for missing sections.
    """
    contents_json = list_repo_contents(owner, repo, path)
    
    try:
        contents = json.loads(contents_json)
        
        # 1. Check if README exists
        readme_item = next((item for item in contents if item.get("name", "").lower().startswith("readme")), None)
        
        # Generate context from the rest of the files in the directory
        readme_name = readme_item.get("name", "") if readme_item else ""
        root_files_context = [
            {"name": item.get("name"), "type": item.get("type"), "size": item.get("size", 0)}
            for item in contents if item.get("type") in ["file", "dir"] and item.get("name") != readme_name
        ]

        if readme_item:
            # 2. If it exists, read its content
            existing_content = read_file_content(owner, repo, os.path.join(path, readme_item.get("name")))
            
            return json.dumps({
                "status": "README_EXISTS_NEEDS_ANALYSIS",
                "existing_readme_content": existing_content,
                "root_files_context": root_files_context
            }, indent=2)

        else:
            # 3. If it doesn't exist, proceed with the "NO_README_FOUND" logic
            return json.dumps({
                "status": "NO_README_FOUND",
                "root_files_context": root_files_context,
                "suggestion_needed": "true"
            }, indent=2)

    except Exception as e:
        return f"ERROR: An unexpected error occurred during README analysis: {e}"


@mcp.tool()
def find_readme_targets(owner: str, repo: str, base_path: str = "") -> str:
    """
    Scans a directory (one level deep) for subdirectories that contain code 
    but do not have a README file, suggesting paths for the agent to analyze.
    """
    contents_json = list_repo_contents(owner, repo, base_path)
    
    try:
        contents = json.loads(contents_json)
        targets = []
        subdirs_to_check_further = []
        
        # Identify directories (folders)
        subdirs = [item for item in contents if item.get("type") == "dir"]
        
        for subdir in subdirs:
            subdir_path = os.path.join(base_path, subdir['name']).replace('\\', '/')
            
            # List contents of the subdirectory
            subdir_contents_json = list_repo_contents(owner, repo, subdir_path)
            subdir_contents = json.loads(subdir_contents_json)
            
            # Check for README and files in the subdirectory
            has_readme = any(item.get("name", "").lower().startswith("readme") for item in subdir_contents)
            has_code_files = any(item.get("type") == "file" for item in subdir_contents)
            
            if has_code_files and not has_readme:
                targets.append(subdir_path)
            
            subdirs_to_check_further.append(subdir_path)


        return json.dumps({
            "status": "SCAN_COMPLETE",
            "targets_identified": targets,
            "subdirectories_scanned": subdirs_to_check_further
        }, indent=2)

    except Exception as e:
        return f"ERROR: Failed during target identification: {e}"


# --- PULL REQUEST WORKFLOW TOOLS ---

@mcp.tool()
def create_branch(owner: str, repo: str, new_branch: str, base_branch: str = "main") -> str:
    """Creates a new branch from a base branch."""
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token: return "ERROR: GITHUB_TOKEN is not set..."
    ref_url = f"https://api.github.com/repos/{owner}/{repo}/git/ref/heads/{base_branch}"
    headers = {"Authorization": f"token {github_token}", "Accept": "application/vnd.github.v3+json"}
    try:
        ref_response = requests.get(ref_url, headers=headers); ref_response.raise_for_status()
        base_sha = ref_response.json()["object"]["sha"]
    except Exception as e: return f"ERROR: Failed to get SHA for base branch: {e}"
    create_ref_url = f"https://api.github.com/repos/{owner}/{repo}/git/refs"
    payload = {"ref": f"refs/heads/{new_branch}", "sha": base_sha}
    try:
        create_response = requests.post(create_ref_url, headers=headers, data=json.dumps(payload)); create_response.raise_for_status()
        return f"SUCCESS: Branch '{new_branch}' created successfully from '{base_branch}'."
    except Exception as e: return f"ERROR: Failed to create branch: {e}"


@mcp.tool()
def commit_file_to_github(owner: str, repo: str, path: str, content: str, branch: str = "main", commit_message: str = "Feat: Add file via ADK agent") -> str:
    """Creates or updates a file on a specified branch."""
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token: return "ERROR: GITHUB_TOKEN is not set..."
    if not all([owner, repo, path, content]): return "ERROR: Missing required fields."
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    headers = {"Authorization": f"token {github_token}", "Accept": "application/vnd.github.v3+json"}
    encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
    payload = {"message": commit_message, "content": encoded_content, "branch": branch}
    try:
        response = requests.put(url, headers=headers, data=json.dumps(payload)); response.raise_for_status()
        return json.dumps({"status": "SUCCESS", "message": f"Successfully committed '{path}' to branch '{branch}'.", "commit_sha": response.json().get('commit', {}).get('sha')})
    except Exception as e: return f"ERROR: Failed to commit file: {e}"


@mcp.tool()
def create_pull_request(owner: str, repo: str, title: str, head_branch: str, base_branch: str = "main", body: str = "Pull Request created by an ADK agent.") -> str:
    """Creates a pull request from the 'head_branch' to the 'base_branch'."""
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token: return "ERROR: GITHUB_TOKEN is not set..."
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    headers = {"Authorization": f"token {github_token}", "Accept": "application/vnd.github.v3+json"}
    payload = {"title": title, "head": head_branch, "base": base_branch, "body": body}
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload)); response.raise_for_status()
        pr_info = response.json()
        return json.dumps({"status": "PR_CREATED", "number": pr_info.get("number"), "html_url": pr_info.get("html_url"), "message": f"Successfully created Pull Request #{pr_info.get('number')}."})
    except Exception as e: return f"ERROR: Failed to create PR: {e}"


# --- Main execution block to start the server ---
if __name__ == "__main__":
    try:
        mcp.run()
    except Exception as e:
        print(f"FATAL MCP CRASH: {e}", file=sys.stderr)
        sys.exit(1)