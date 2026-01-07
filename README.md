# gemini_enterprise_adk_examples

This repository contains examples demonstrating the use of the Gemini Enterprise ADK.

## Project Structure

Here's a brief overview of the key files in this repository:

*   `agent.py`: This file defines a `GitHubExpert` agent that specializes in generating high-quality READMEs for GitHub repositories, utilizing various tools for repository analysis, branch creation, file committing, and pull request generation.
*   `currencyagent.py`: This file implements a specialized `LlmAgent` for currency conversions, which uses a `get_exchange_rate` tool to answer currency-related queries and politely declines unrelated questions.
*   `test server.py`: This file sets up an MCP (Multi-tool Co-operation Protocol) server named "GitHubTools" and defines several tools for interacting with the GitHub API, including reading file content, getting project dependencies, retrieving repository information, listing repository contents, analyzing and suggesting READMEs, finding README targets, creating branches, committing files, and creating pull requests.

## Getting Started

Further instructions will be added here.
