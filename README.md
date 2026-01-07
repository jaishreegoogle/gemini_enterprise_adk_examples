# Gemini Enterprise ADK Examples

This repository contains examples demonstrating the use of the Gemini Enterprise ADK.

## Project Structure

Here's an overview of the key files and their purposes:

*   **`agent.py`**: This file defines the `GitHubExpert` AI agent, which specializes in GitHub documentation, including a mandatory workflow for creating/updating READMEs and handling pull requests.
*   **`currencyagent.py`**: This file defines a specialized `LlmAgent` for currency conversions, utilizing a `get_exchange_rate` tool and configured to be A2A-compatible.
*   **`test server.py`**: This file (which is actually `mcp_server.py` based on its content) implements an MCP (Multi-tool Communication Protocol) server named "GitHubTools" and exposes several tools for interacting with GitHub, such as reading file content, getting project dependencies, retrieving repository information, listing repository contents, analyzing and suggesting READMEs, finding README targets, creating branches, committing files, and creating pull requests.
*   **`__init__.py`**: This file imports `root_agent` from the `agent` module, likely serving to initialize the package or make the agent accessible.
*   **`.github/`**: This directory likely contains GitHub-specific configurations, such as workflows for GitHub Actions.
*   **`localtest.md`**: This is a Markdown file, likely containing local testing notes or documentation.

## Getting Started

(Further sections like Installation, Usage, Contributing would go here, but for this initial README generation, we'll focus on the structure and file summaries.)