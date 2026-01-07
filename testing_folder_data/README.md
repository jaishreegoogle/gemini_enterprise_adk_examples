# Documentation for testing_folder_data

This directory contains core components for an AI agent designed for GitHub documentation and an MCP server that exposes GitHub API functionalities.

## Project Structure

### `agent.py`
This file defines a `root_agent` using the `google.adk.agents.Agent` class. This agent is designed to act as a GitHub Documentation Architect, specializing in repository analysis, code summarization, and PR orchestration. It's configured to use a specific model (`gemini-2.5-flash`) and integrates with a `McpToolset` for GitHub operations.

### `mcp_server.py`
This file implements a Micro-Controller Platform (MCP) server using `FastMCP` to expose various GitHub API functionalities as tools. It acts as an intermediary, allowing an agent to interact with GitHub repositories by providing functions for listing branches, repository contents, reading file content, getting project dependencies, retrieving repository information, analyzing READMEs, listing directories, creating branches, committing files, and creating pull requests. It handles GitHub authentication using a `GITHUB_TOKEN`.