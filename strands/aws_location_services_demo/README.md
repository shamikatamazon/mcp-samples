# TravelGuide AI Web Application

This web application provides a browser-based interface for interacting with the TravelGuide AI assistant, which uses AWS Location Services through MCP (Modular Capability Provider).

## Features

- Web-based interface for querying the TravelGuide AI assistant
- Real-time status updates on agent initialization
- Display of response metrics (tokens used, execution time, tools used)
- Responsive design for desktop and mobile browsers

## Prerequisites

- Python 3.8+
- MCP server running locally on port 8080
- AWS credentials configured for Bedrock access

## Installation

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. Make sure your MCP server is running:

```bash
# Example command to start MCP server (adjust as needed)
# This would typically be in a separate terminal
cd aws-location-mcp-server/
fastmcp run server.py:mcp --transport sse --port 8080 --host 0.0.0.0 --log-level debug
```

Download and install [Jaeger](https://www.jaegertracing.io/) on your instance

Start the Jaeger daemon

## Usage

1. Start the web application:

```bash
python awsLocationWithMCP_web.py
```

2. Open your browser and navigate to:

```
http://localhost:8081
```

3. Wait for the agent to initialize (indicated by the status bar)

4. Enter your travel-related query in the text area and click "Ask TravelGuide"

## Example Queries

- "I'm travelling to LA from Seattle by car, what are some sights that I should see on the way?"
- "I would like to drive from Seattle to Dallas in 10 hours, is it possible?"
- "Create a 3-day itinerary for visiting New York City on a budget"
- "What are the best hiking trails near Portland, Oregon?"

## Notes

- The application uses the Nova Pro model from Amazon Bedrock by default
- The agent initialization may take a few moments when first starting the application
- All queries are processed through the MCP server which provides access to AWS Location Services