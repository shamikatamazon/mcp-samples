import logging
import asyncio
from typing import Optional
from typing import List, Dict, Any
from contextlib import AsyncExitStack
import boto3
from mcp import ClientSession, StdioServerParameters, Resource
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv
from mcp.types import Tool
from fastmcp import Client
import time


MODEL_ID = "us.amazon.nova-pro-v1:0"


# Configure logging at the beginning of the file
def setup_logger():
    logger = logging.getLogger('WeatherClient')
    logger.setLevel(logging.INFO)
    
    # Remove any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create console handler with formatting
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    return logger

logger = setup_logger()

class MCPClient:
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.bedrock = boto3.client('bedrock-runtime')
        self.model_id = MODEL_ID
        
    @staticmethod
    def parse_text_to_dict(text: str) -> Dict[str, Any]:
        logger.info("Parsing text to dictionary")
        logger.debug("Input text: %s", text)

        result = {}
        for line in text.strip().split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                result[key.strip().lower()] = value.strip()
            else:
                result["text"] = text
        return result

    @staticmethod
    def convert_tool_to_json_spec(tool: Tool) -> dict:
        logger.info("Converting tool to JSON specification")
        # Rest of the method remains the same, just replace prints with logger
        properties = {}
        for prop_name, prop_details in tool.inputSchema.get('properties', {}).items():
            prop_type = prop_details.get('type', 'string')
            description = ""
            if prop_name in tool.description:
                for line in tool.description.split('\n'):
                    if prop_name in line:
                        description = line.strip()
                        break

            properties[prop_name] = {
                "type": prop_type,
                "description": description
            }

        tool_spec = {
            "name": tool.name,
            "description": tool.description,
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": properties,
                    "required": tool.inputSchema.get('required', [])
                }
            }
        }
        return tool_spec

    @staticmethod
    def convert_content_to_json(content_obj: Any, tool_use_id: str = "default_tool_id") -> Dict[str, Any]:
        logger.info("Converting content to JSON format")
        logger.info("Content object: %s", content_obj)
        
        json_contents = []
        
        if isinstance(content_obj, list):
            for item in content_obj:
                if hasattr(item, 'text'):
                    parsed_data = {"text": item.text}
                    json_contents.append(parsed_data)
        elif hasattr(content_obj, 'text'):
            parsed_data = {"text": content_obj.text}
            json_contents.append(parsed_data)

        status = "error" if getattr(content_obj, 'isError', False) else "success"
        
        json_structure = {
            "role": "user",
            "content": [
                {
                    "toolResult": {
                        "toolUseId": tool_use_id,
                        "content": json_contents,
                        "status": status
                    }
                }
            ]
        }

        logger.info("tool response: %s", json_structure)
        return json_structure

    async def process_query(self, query: str, client) -> str:
        logger.info("Processing query: %s", query)
        
        tools = await client.list_tools()
        for tool in tools:
            logger.info("Available tool: %s", tool.name)

        list_of_tools = []
        for tool in tools:
            tools_json = MCPClient.convert_tool_to_json_spec(tool)
            toolSpec = {"toolSpec": tools_json}
            list_of_tools.append(toolSpec)

        available_tools = {"tools": list_of_tools}
        logger.debug("Available tools configuration: %s", available_tools)

        messages = [
            {
                "role": "user",
                "content": [{"text": query}]
            }
        ]

        system_prompts = [{"text": """You are an AI assistant that can use tools to help users. When using tools, format your responses clearly and explain what you're doing."""}]
        final_text = []

        while True:
            response = self.bedrock.converse(
                modelId=self.model_id,
                messages=messages,
                system=system_prompts,
                toolConfig=available_tools,
            )

            logger.debug("Bedrock response: %s", response)
            output_message = response['output']['message']
            messages.append(output_message)

            for content in output_message['content']:
                if 'text' in content:
                    final_text.append(content['text'])
                elif 'toolUse' in content:
                    tool_name = content['toolUse']['name']
                    tool_args = content['toolUse']['input']
                    
                    logger.info("Executing tool: %s with arguments: %s", tool_name, tool_args)
                    final_text.append(f"Obtaining information from {tool_name} with args {tool_args}")

                    result = await client.call_tool(tool_name, tool_args)
                    logger.debug("Tool execution result: %s", result)
                    
                    toolResult = MCPClient.convert_content_to_json(result, content['toolUse']['toolUseId'])
                    logger.debug("Tool result in JSON format: %s", toolResult)
                    messages.append(toolResult)
            
            if not any('toolUse' in content for content in output_message['content']):
                break

        return "\n".join(final_text)

    async def chat_loop(self, client):
        logger.info("MCP Client Started!")
        logger.info("Type your queries or 'quit' to exit.")

        while True:
            try:
                query = input("\nQuery: ").strip()

                if query.lower() == 'quit':
                    logger.info("Exiting chat loop")
                    break

                response = await self.process_query(query, client)
                #logger.info("Response: %s", response)
                print("\n" + response)

            except Exception as e:
                logger.error("Error in chat loop: %s", str(e))

    async def cleanup(self):
        logger.info("Cleaning up resources")
        await self.exit_stack.aclose()

async def main():
    if len(sys.argv) < 2:
        logger.error("Usage: python client.py <path_to_server_script>")
        sys.exit(1)

    mcp_client = MCPClient()
    client = Client("http://localhost:8080/sse")

    async with client:
        await mcp_client.chat_loop(client)

if __name__ == "__main__":
    import sys
    asyncio.run(main())
