# --- File: agent.py (Final Version with Subfolder Support) ---
import os
import pathlib
import sys 

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.genai import types

from google.adk.tools.mcp_tool import McpToolset 
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams 
from mcp import StdioServerParameters 


# --- 1. Path and Environment Setup (CRITICAL FIXES INCLUDED) ---

current_dir = pathlib.Path(__file__).parent
mcp_server_path = str(current_dir / "mcp_server.py")

github_token_value = os.getenv("GITHUB_TOKEN")
mcp_environment = {}

if github_token_value:
    mcp_environment["GITHUB_TOKEN"] = github_token_value
else:
    print("FATAL ERROR: GITHUB_TOKEN environment variable is not set.", file=sys.stderr)
    print("Please set GITHUB_TOKEN (e.g., using 'export') before starting the agent.", file=sys.stderr)
    sys.exit(1)


# --- 2. Define the Root Agent ---
root_agent = Agent(
    name="GitHubExpert",
    description="An AI agent specializing in fetching real-time data from GitHub and assisting with professional documentation workflows.",
    
    model=LiteLlm("gemini-2.5-flash"),
    
    instruction="""
    You are an expert **GitHub Documentation Architect**. Your expertise includes ensuring every code-containing directory has a high-quality README.
    
    1. **Project Discovery:** If asked to work on documentation generally, your **first action** must be to call **`find_readme_targets`** on the root path ("") to identify all subfolders that need a README. You must then process those targets.
    
    2. **Core Workflow (MANDATORY STEPS for EACH TARGET PATH):** For every path you identify or are given by the user, you must execute the full, high-quality PR workflow:
        * **Step 2a (Analysis):** Call `analyze_and_suggest_readme` for the specific target path (e.g., 'src/api/').
        * **Step 2b (Branching):** Call `create_branch` (e.g., 'feature-readme-src-api').
        * **Step 2c (Dependency Check):** **ALWAYS** call **`get_project_dependencies`**. You should infer the correct path for the dependency file (e.g., if checking 'src/api', first check 'src/api/requirements.txt', then check the root 'requirements.txt').
        * **Step 2d (Generation & Commit):** This depends on the analysis:
            * **Creation/Update:** Generate or rewrite the README content to the highest quality, using all context (file list, dependency content). The file path for commit must be correct (e.g., 'src/api/README.md').
            * Call `commit_file_to_github` with the correct file path and the new branch name.
        * **Step 2e (PR Creation):** Immediately call **`create_pull_request`** for the path's changes.
    
    3. **Final Output:** If multiple paths were processed, summarize the results (e.g., "Created 3 PRs for /src/models, /src/api, and /").
    """,
    
    # 3. Tools: McpToolset configuration
    tools=[
        McpToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command='python',
                    args=[mcp_server_path], 
                    environment=mcp_environment, 
                ),
            ),
        )
    ],
    
    # 4. Optional: Model Configuration
    generate_content_config=types.GenerateContentConfig(
        temperature=0.4, 
    )
)