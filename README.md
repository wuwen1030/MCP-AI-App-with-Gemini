# MCP: Build AI App with Gemini

A demonstration project for building MCP-enabled chatbots with Google Gemini integration and a custom research MCP server.

> Inspired by [MCP: Build Rich-Context AI Apps with Anthropic](https://learn.deeplearning.ai/courses/mcp-build-rich-context-ai-apps-with-anthropic).  
> This project provides an alternative for developers who cannot access Anthropic's Claude API in certain regions.

## Overview

This project provides a complete demonstration of how to build both MCP (Model Context Protocol) clients and servers. It showcases the full MCP ecosystem by implementing:

**MCP Client Side:**
- An AI-powered chatbot that connects to multiple MCP servers
- Integration with Google's Gemini 2.5 Flash for intelligent conversation
- Dynamic loading of different MCP servers from configuration files
- Automatic tool discovery and function calling across multiple servers

**MCP Server Side:**
- A custom research server for arXiv paper search and management
  - [x] **Tools**: Implements `search_papers()` and `extract_info()` functions for paper research
  - [ ] **Resources**: Manages paper storage and retrieval from local file system
  - [ ] **Prompt Templates**: Provides structured templates for research queries and paper analysis

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


## Acknowledgments

- [Model Context Protocol (MCP)](https://github.com/modelcontextprotocol) - For the protocol specification and tools
- [Google Gemini](https://deepmind.google/technologies/gemini/) - For the AI model
- [arXiv](https://arxiv.org/) - For providing access to research papers
