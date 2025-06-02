# TravelGuide AI Web Application

This web application provides a browser-based interface for interacting with the TravelGuide AI assistant, which uses AWS Location Services through MCP.

## Features

- Web-based interface for querying the TravelGuide AI assistant
- User authentication for secure access
- Real-time status updates on agent initialization
- Display of response metrics (tokens used, execution time, tools used)
- Responsive design for desktop and mobile browsers

## Prerequisites

- Python 3.8+
- MCP server running locally on port 8080
- AWS credentials configured for Bedrock access

## Local Installation

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

3. Set environment variables for authentication:

```bash
export FLASK_SECRET_KEY="your-secret-key-here"
export ADMIN_PASSWORD="your-admin-password"
```

## Local Usage

1. Start the web application:

```bash
python awsLocationWithMCP_web.py
```

2. Open your browser and navigate to:

```
http://localhost:8081
```

3. Log in with username "admin" and the password you set in the environment variable

4. Wait for the agent to initialize (indicated by the status bar)

5. Enter your travel-related query in the text area and click "Ask TravelGuide"

## AWS Deployment

You can deploy this application to AWS using the provided CloudFormation template:

1. Navigate to the AWS CloudFormation console

2. Create a new stack and upload the `cloudformation.yaml` file

3. Fill in the required parameters:
   - VPC ID
   - Subnet IDs (at least two, in different AZs)
   - EC2 Key Pair name
   - Instance type (t3.medium recommended)
   - Admin password (for web app login)
   - Flask secret key (for session encryption)

4. Create the stack and wait for it to complete

5. Access your application using the CloudFront URL provided in the stack outputs

## Example Queries

- "I'm travelling to LA from Seattle by car, what are some sights that I should see on the way?"
- "I would like to drive from Seattle to Dallas in 10 hours, is it possible?"
- "Create a 3-day itinerary for visiting New York City on a budget"
- "What are the best hiking trails near Portland, Oregon?"

## Notes

- The application uses the Nova Pro model from Amazon Bedrock by default
- The agent initialization may take a few moments when first starting the application
- All queries are processed through the MCP server which provides access to AWS Location Services
- For production use, consider implementing a more robust authentication system