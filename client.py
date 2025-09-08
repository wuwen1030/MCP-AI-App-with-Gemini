import json
from dotenv import load_dotenv
from google import genai
from google.genai.chats import Chat
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from typing import Dict, List, TypedDict
import asyncio
import nest_asyncio
from contextlib import AsyncExitStack
from utils import clean_schema_for_gemini

nest_asyncio.apply()

load_dotenv()

MODEL_ID = "gemini-2.5-flash"

class ToolDefinition(TypedDict):
    name: str
    description: str
    parameters: dict


class MCP_ChatBot:
    def __init__(self):
        self.sessions = {}
        self.exit_stack = AsyncExitStack()
        self.gemini: genai.Client = genai.Client()
        self.chat: Chat = None
        self.available_tools: List[ToolDefinition] = []
        self.available_prompts = []

    async def connect_to_server(self, server_name: str, server_config: dict) -> None:
        """Connect to a MCP server"""
        try:
            server_params = StdioServerParameters(**server_config)
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            read, write = stdio_transport

            session = await self.exit_stack.enter_async_context(
                ClientSession(read, write)
            )

            await session.initialize()
            
            try:
                # list available tools
                response = await session.list_tools()
                for tool in response.tools: # new
                    self.sessions[tool.name] = session

                    # only keep the necessary fields from the tool input schema
                    # becuase there are some fields that are not supported by gemini
                    # there will be runtime errors if we use tool.inputSchema directly
                    input_schema = tool.inputSchema if tool.inputSchema else {}
                    parameters = clean_schema_for_gemini(input_schema)
                    self.available_tools.append({
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": parameters
                    })

                # List available prompts
                prompts_response = await session.list_prompts()
                if prompts_response and prompts_response.prompts:
                    for prompt in prompts_response.prompts:
                        self.sessions[prompt.name] = session
                        self.available_prompts.append({
                            "name": prompt.name,
                            "description": prompt.description,
                            "arguments": prompt.arguments
                        })
                
                # List available resources
                resources_response = await session.list_resources()
                if resources_response and resources_response.resources:
                    for resource in resources_response.resources:
                        resource_uri = str(resource.uri)
                        self.sessions[resource_uri] = session        
                
            except Exception as e:
                print(f"Error {e}")

        except Exception as e:
            print(f"Failed to connect to {server_name}: {e}")

    async def connect_to_servers(self):
        """Connect to all servers"""
        try:
            with open("server_config.json", "r") as f:
                data = json.load(f)
                servers = data.get("mcpServers", {})
                for server_name, server_config in servers.items():
                    await self.connect_to_server(server_name, server_config)
        except Exception as e:
            print(f"Error loading server configuration: {e}")
            raise e

    async def process_query(self, user_input: str):
        response = self.chat.send_message(user_input)
        process_query = True
        while process_query:
            function_call = response.candidates[0].content.parts[0].function_call
            if function_call:
                tool_name = function_call.name
                tool_args = function_call.args

                print(f"Calling tool {tool_name} with args {tool_args}")
                    
                session = self.sessions.get(tool_name)
                tool_result = await session.call_tool(tool_name, tool_args)
                
                # response to the tool call
                response = self.chat.send_message(
                    genai.types.Part(
                        function_response=genai.types.FunctionResponse(
                            name=tool_name,
                            response={
                                'result': tool_result.content
                            }
                        )
                    )
                )
                
                parts = response.candidates[0].content.parts
                if len(parts) == 1 and parts[0].text:
                    print(f"Gemini:\n{response.text}\n")
                    process_query = False
            else:
                print(f"Gemini:\n{response.text}\n")
                process_query = False

    async def get_resource(self, resource_uri):
        session = self.sessions.get(resource_uri)
        
        # Fallback for papers URIs - try any papers resource session
        if not session and resource_uri.startswith("papers://"):
            for uri, sess in self.sessions.items():
                if uri.startswith("papers://"):
                    session = sess
                    break
            
        if not session:
            print(f"Resource '{resource_uri}' not found.")
            return
        
        try:
            result = await session.read_resource(uri=resource_uri)
            if result and result.contents:
                print(f"\nResource: {resource_uri}")
                print("Content:")
                print(result.contents[0].text)
            else:
                print("No content available.")
        except Exception as e:
            print(f"Error: {e}")
    
    async def list_prompts(self):
        """List all available prompts."""
        if not self.available_prompts:
            print("No prompts available.")
            return
        
        print("\nAvailable prompts:")
        for prompt in self.available_prompts:
            print(f"- {prompt['name']}: {prompt['description']}")
            if prompt['arguments']:
                print(f"  Arguments:")
                for arg in prompt['arguments']:
                    arg_name = arg.name if hasattr(arg, 'name') else arg.get('name', '')
                    print(f"    - {arg_name}")
    
    async def execute_prompt(self, prompt_name, args):
        """Execute a prompt with the given arguments."""
        session = self.sessions.get(prompt_name)
        if not session:
            print(f"Prompt '{prompt_name}' not found.")
            return
        
        try:
            result = await session.get_prompt(prompt_name, arguments=args)
            if result and result.messages:
                prompt_content = result.messages[0].content
                
                # Extract text from content (handles different formats)
                if isinstance(prompt_content, str):
                    text = prompt_content
                elif hasattr(prompt_content, 'text'):
                    text = prompt_content.text
                else:
                    # Handle list of content items
                    text = " ".join(item.text if hasattr(item, 'text') else str(item) 
                                  for item in prompt_content)
                
                print(f"\nExecuting prompt '{prompt_name}'...")
                await self.process_query(text)
        except Exception as e:
            print(f"Error: {e}")
    
    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Chatbot Started!")
        print("Type your queries or 'quit' to exit.")
        print("Use @folders to see available topics")
        print("Use @<topic> to search papers in that topic")
        print("Use /prompts to list available prompts")
        print("Use /prompt <name> <arg1=value1> to execute a prompt")

        self.chat = self.gemini.chats.create(
            model=MODEL_ID,
            config=genai.types.GenerateContentConfig(
                max_output_tokens=2024,
                tools=[genai.types.Tool(function_declarations=self.available_tools)]
            )
        )

        while True:
            try:
                user_input = input("You: ").strip()
                if not user_input:
                    continue

                if user_input.lower() == 'quit':
                    print("Exiting chat. Goodbye!")
                    break
                
                # Check for @resource syntax first
                if user_input.startswith("@"):
                    topic = user_input[1:]
                    if topic == "folders":
                        resource_uri = "papers://folders"
                    else:
                        resource_uri = f"papers://{topic}"
                    await self.get_resource(resource_uri)
                    continue

                # Check fo /command syntax
                if user_input.startswith('/'):
                    parts = user_input.split()
                    command = parts[0].lower()
                    
                    if command == '/prompts':
                        await self.list_prompts()
                    elif command == '/prompt':
                        if len(parts) < 2:
                            print("Usage: /prompt <name> <arg1=value1> <arg2=value2>")
                            continue
                        
                        prompt_name = parts[1]
                        args = {}
                        
                        # Parse arguments
                        for arg in parts[2:]:
                            if '=' in arg:
                                key, value = arg.split('=', 1)
                                args[key] = value
                        
                        await self.execute_prompt(prompt_name, args)
                    else:
                        print(f"Unknown command: {command}")
                    continue

                await self.process_query(user_input)
            except Exception as e:
                print(f"An error occurred: {e}")

    async def cleanup(self): # new
        """Cleanly close all resources using AsyncExitStack."""
        await self.exit_stack.aclose()

async def main():
    chatbot = MCP_ChatBot()
    try:
        await chatbot.connect_to_servers()
        await chatbot.chat_loop()
    finally:
        await chatbot.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
