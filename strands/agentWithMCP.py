from strands import Agent, tool
import os
from strands.telemetry.tracer import get_tracer
from strands.models import BedrockModel
from strands.handlers.callback_handler import PrintingCallbackHandler
from strands.tools.mcp import MCPClient
from mcp.client.sse import sse_client


# Create an agent with default settings

os.environ["STRANDS_OTEL_ENABLE_CONSOLE_EXPORT"] = "false"


tracer = get_tracer(
    service_name="mcp-agent-service",
    otlp_endpoint="http://localhost:4318",
)

nova_agent_model = BedrockModel(
    model_id="us.amazon.nova-lite-v1:0",
    temperature=0,
    max_tokens=1000,
    top_p=1,
    streaming=False,
)


# Connect to an MCP server using SSE transport
sse_mcp_client = MCPClient(lambda: sse_client("http://localhost:8080/sse"))

# Create an agent with MCP tools
with sse_mcp_client:
    # Get the tools from the MCP server
    tools = sse_mcp_client.list_tools_sync()

    # Create an agent with these tools
    weather_agent = Agent(system_prompt="You are an expert weather forecaster and can predict the weather for a place in the USA. Use the tools provided to determine the weather",
        tools=tools,
        model = nova_agent_model)

    print(weather_agent.model.config)

    # Ask the agent a question
    result = weather_agent("I'm travelling to LA tomorrow, what should i pack")

    print(f"\nTotal tokens: {result.metrics.accumulated_usage['totalTokens']}")
    print(f"\nExecution time: {sum(result.metrics.cycle_durations):.2f} seconds")
    print(f"\nTools used: {list(result.metrics.tool_metrics.keys())}")