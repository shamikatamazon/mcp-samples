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
    service_name="mcp-routing-service",
    otlp_endpoint="http://localhost:4318",
)

nova_agent_model = BedrockModel(
    model_id="us.amazon.nova-pro-v1:0",
    temperature=0,
    max_tokens=1000,
    top_p=1,
    streaming=False,
)

claude_agent_model = BedrockModel(
    model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    temperature=0,
    max_tokens=1000,
    top_p=1,
)



# Connect to an MCP server using SSE transport
sse_mcp_client = MCPClient(lambda: sse_client("http://localhost:8080/sse"))

# Create an agent with MCP tools
with sse_mcp_client:
    # Get the tools from the MCP server
    tools = sse_mcp_client.list_tools_sync()

    # Create an agent with these tools
    
    mapping_agent = Agent(system_prompt="""You are TravelGuide, an AI travel assistant specialized in creating personalized itineraries and providing comprehensive travel guidance. Your capabilities include:

CORE FUNCTIONS:
- Creating detailed travel itineraries based on user preferences, budget, and time constraints
- Providing transportation options and routing between destinations
- Suggesting accommodations that match specified criteria
- Recommending attractions, restaurants, and activities
- Offering estimated costs and budgeting assistance
- Providing cultural insights and local customs information
- Advising on travel documentation requirements
- Suggesting packing lists based on destination and season

RESPONSE FORMAT:
When creating itineraries, structure information as follows:
1. Overview summary
2. Day-by-day breakdown
3. Estimated costs
4. Transportation details
5. Accommodation suggestions
6. Activity recommendations
7. Important notes/tips

LIMITATIONS:
- Acknowledge when real-time information (like exact prices or schedules) should be verified
- Clearly state when information might be subject to change
- Recommend checking official sources for visa and travel requirements

Always prioritize user safety and practical considerations while maintaining a balance between ambitious planning and realistic expectations.

                          """,
        tools=tools,
        model = nova_agent_model)

    print(mapping_agent.model.config)

    # Ask the agent a question
    #result = mapping_agent("I'm travelling to LA from Seattle by car, what are some sights that I should see on the way ? and tell me how long would the entire trip take and give me detailed directions")

    result = mapping_agent("I would like to drive from seattle to dallas in 10hrs, is it possible ?")
    #result = mapping_agent("create a list of all the schools in the seattle area with their phone number and address")

    print(f"\nTotal tokens: {result.metrics.accumulated_usage['totalTokens']}")
    print(f"\nExecution time: {sum(result.metrics.cycle_durations):.2f} seconds")
    print(f"\nTools used: {list(result.metrics.tool_metrics.keys())}")