from strands import Agent
import os
from strands.telemetry.tracer import get_tracer
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient
from mcp.client.sse import sse_client
from flask import Flask, render_template, request, jsonify
import threading
import time

# Configure environment
os.environ["STRANDS_OTEL_ENABLE_CONSOLE_EXPORT"] = "false"

# Initialize tracer
tracer = get_tracer(
    service_name="mcp-routing-service",
    otlp_endpoint="http://localhost:4318",
)

# Configure models
nova_agent_model = BedrockModel(
    model_id="us.amazon.nova-pro-v1:0",
    temperature=0,
    max_tokens=1000,
    top_p=0.2,
    streaming=False,
)

claude_agent_model = BedrockModel(
    model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    temperature=0,
    max_tokens=1000,
    top_p=0.2,
)

# Initialize Flask app
app = Flask(__name__)

# Global variables
agent = None
mcp_client = None
tools = None
agent_ready = False

# System prompt for the travel assistant
SYSTEM_PROMPT = """You are TravelGuide, an AI travel assistant specialized in creating personalized itineraries and providing comprehensive travel guidance. Your capabilities include:

CORE FUNCTIONS:
- Creating detailed travel itineraries based on user preferences, budget, and time constraints using tools
- Providing transportation options and routing between destinations using tools
- Suggesting accommodations that match specified criteria using tools
- Recommending attractions, restaurants, and activities using tools
- Offering estimated costs and budgeting assistance
- Providing cultural insights and local customs information 
- Advising on travel documentation requirements 
- Suggesting packing lists based on destination and season

RESPONSE FORMAT:
When creating itineraries, structure information as follows:
1. Overview summary
2. Day-by-day breakdown

LIMITATIONS:
- Acknowledge when real-time information (like exact prices or schedules) should be verified
- Clearly state when information might be subject to change
- Recommend checking official sources for visa and travel requirements

Always prioritize user safety and practical considerations while maintaining a balance between ambitious planning and realistic expectations.

you will be provided a list of tools to satisfy the query. **Always** use the tools to answer queries, do not use your internal knowledge

if you use the search_nearby tool, places should be mapped to one of the following categories and only use one category at a time when quering the function
 'airport',
    'bank',
    'hospital',
    'hotel',
    'restaurant',
    'shopping_mall',
    'grocery',
    'pharmacy',
    'gas_station',
    'police_station',
    'school',
    'post_office',
    'train_station',
    'bus_station',
    'parking',
    'coffee_shop',
    'atm',
    'convenience_store',
    'park-recreation_area',
    'tourist_attraction'

    
    PROCESS :
    When answering any query, first check if you need to calculate a route using the calculate_route tool, once its done, use the route information
    to get any other information that is required.
    
"""

def initialize_agent():
    """Initialize the MCP client and agent in a separate thread."""
    global agent, mcp_client, tools, agent_ready
    
    # Connect to an MCP server using SSE transport
    mcp_client = MCPClient(lambda: sse_client("http://localhost:8080/sse"))
    
    # Create an agent with MCP tools
    with mcp_client:
        # Get the tools from the MCP server
        tools = mcp_client.list_tools_sync()
        
        # Create an agent with these tools
        agent = Agent(
            system_prompt=SYSTEM_PROMPT,
            tools=tools,
            model=claude_agent_model
        )
        
        agent_ready = True
        print("Agent initialized and ready to use")

# Start agent initialization in a separate thread
threading.Thread(target=initialize_agent).start()

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask_agent():
    """Process user query and return agent response."""
    if not agent_ready:
        return jsonify({
            'response': 'Agent is still initializing. Please try again in a few moments.',
            'metrics': None
        })
    
    user_query = request.json.get('query', '')
    if not user_query:
        return jsonify({
            'response': 'Please provide a query.',
            'metrics': None
        })
    
    try:
        # Create a completely new connection for each request with a unique session ID
        session_id = f"session_{time.time()}"
        connection_url = f"http://localhost:8080/sse?session={session_id}"
        
        # Create a fresh MCP client with the unique session
        fresh_mcp_client = MCPClient(lambda: sse_client(connection_url))
        
        # Process the query with a fresh agent instance
        with fresh_mcp_client:
            # Get the tools from the MCP server
            fresh_tools = fresh_mcp_client.list_tools_sync()
            
            # Create a new agent instance with memory disabled
            fresh_agent = Agent(
                system_prompt=SYSTEM_PROMPT,
                tools=fresh_tools,
                model=nova_agent_model
            )
            
            # Process the query
            result = fresh_agent(user_query)
            
            # Extract metrics
            metrics = {
                'total_tokens': result.metrics.accumulated_usage.get('totalTokens', 0),
                'execution_time': round(sum(result.metrics.cycle_durations), 2),
                'tools_used': list(result.metrics.tool_metrics.keys())
            }
            
            # Extract the response text
            response_text = str(result)
            
            return jsonify({
                'response': response_text,
                'metrics': metrics
            })
    except Exception as e:
        return jsonify({
            'response': f"Error processing your request: {str(e)}",
            'metrics': None
        })

@app.route('/status')
def agent_status():
    """Check if the agent is ready."""
    return jsonify({'ready': agent_ready})

if __name__ == '__main__':
    # Wait for agent to initialize before starting the server
    print("Initializing agent...")
    while not agent_ready and time.sleep(1) is None:
        pass
    
    print("Starting web server...")
    app.run(host='0.0.0.0', port=8081, debug=True)