# MCP: Build AI App with Gemini

A demonstration project for building MCP-enabled chatbots with Google Gemini integration and a custom research MCP server.

> Inspired by [MCP: Build Rich-Context AI Apps with Anthropic](https://learn.deeplearning.ai/courses/mcp-build-rich-context-ai-apps-with-anthropic).  
> This project provides an alternative for developers who cannot access Anthropic's Claude API in certain regions.

## Overview

This project provides a complete demonstration of how to build both MCP (Model Context Protocol) clients and servers. It showcases the full MCP ecosystem by implementing:

**MCP Client Side:**
- Chatbot powered by Google Gemini for intelligent conversations.
- Implements MCP core concepts on the client: tools, resources, and prompt templates.
- Connects to multiple MCP servers via a simple configuration file.

**MCP Server Side:**
- A custom research server for arXiv paper search and management
  - [x] **Tools**: `search_papers(topic, max_results)` and `extract_info(paper_id)`
  - [x] **Resources**: Browse saved papers via `papers://folders` and `papers://{topic}`
  - [x] **Prompt Templates**: `generate_search_prompt(topic, num_papers)` for structured literature review

## Installation

### Prerequisites

- Python 3.13+
- Node.js (for filesystem MCP server)
- uv (Python package manager)

### Setup

1. **Clone the repository**:

2. **Install Python dependencies**:
   ```bash
   uv sync
   ```

3. **Set up environment variables**:
   ```bash
   cp env.example .env
   # Edit .env and add your GEMINI_API_KEY
   ```

4. **Get your Gemini API key**:
   - Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
   - Create a new API key
   - Add it to your `.env` file:
     ```
     GEMINI_API_KEY=your_api_key_here
     ```

## Usage

### Running the Chatbot

Start the interactive chatbot:

```bash
uv run client.py
```

The chatbot will:
1. Connect to all configured MCP servers
2. Initialize the Gemini AI model
3. Start an interactive chat session

### Interactive Commands

Inside the chat session, you can use:

- @folders: List available topics that have saved papers (`papers://folders`).
- @<topic>: Show a markdown summary of papers for a topic (`papers://{topic}`). Example: `@agentic_workflows`.
- /prompts: List all available prompt templates.
- /prompt <name> <arg=value> ...: Execute a prompt and let Gemini continue the conversation.
  - Example: `/prompt generate_search_prompt topic="graph neural networks" num_papers=5`

You can also ask questions in natural language. Gemini will automatically call tools the servers expose when appropriate.

### What’s Included

- Research MCP server (`research_server.py`)
  - Tools
    - `search_papers(topic, max_results=5)`: Fetches papers from arXiv and stores metadata locally under `papers/<topic>/papers_info.json`.
    - `extract_info(paper_id)`: Looks up a paper across all topics and returns its saved metadata.
  - Resources
    - `papers://folders`: Lists all topics with saved papers.
    - `papers://{topic}`: Renders a markdown overview of papers saved for that topic.
  - Prompt Templates
    - `generate_search_prompt(topic, num_papers=5)`: Produces a structured research prompt that instructs the model to search, extract, and synthesize findings.

### Multiple Servers

By default, `server_config.json` connects to:

- `filesystem`: Node-based MCP server for local file browsing (requires Node.js). It may not implement all MCP methods (e.g., tools list), which is normal.
- `research`: Python MCP server in this repo for arXiv research workflows.
- `fetch`: Generic HTTP fetch MCP server.

The client handles optional capabilities gracefully, so you might see notices like `[filesystem] tools unsupported: Method not found` when a server doesn’t support a specific method.


## Acknowledgments

- [Model Context Protocol (MCP)](https://github.com/modelcontextprotocol) - For the protocol specification and tools
- [Google Gemini](https://deepmind.google/technologies/gemini/) - For the AI model
- [arXiv](https://arxiv.org/) - For providing access to research papers
