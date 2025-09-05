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
        self.sessions: List[ClientSession] = []
        self.exit_stack = AsyncExitStack()
        self.gemini: genai.Client = genai.Client()
        self.chat: Chat = None
        self.available_tools: List[ToolDefinition] = []
        self.tool_to_session: Dict[str, ClientSession] = {}

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
            self.sessions.append(session)
            
            response = await session.list_tools()
            tools = response.tools
            print(f"\nConnected to {server_name} with tools:", [t.name for t in tools])

            for tool in tools: # new
                self.tool_to_session[tool.name] = session

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
                    
                session = self.tool_to_session[tool_name]
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

    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Chatbot Started!")
        print("Type your queries or 'quit' to exit.")

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
                if user_input.lower() == 'quit':
                    print("Exiting chat. Goodbye!")
                    break
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
