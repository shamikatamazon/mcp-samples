# Weather Application Setup Guide

This guide provides detailed instructions for setting up and running the weather application locally.

## Prerequisites
- Python 3.7 or higher
- uv package manager
- Active internet connection
- Valid AWS credentials

## Installation Steps

### Clone the Repository
```bash
git clone https://github.com/shamikatamazon/mcp-samples.git
cd mcp-samples
```
### Initialize uv for the weather project
```bash
uv init weather
cd weather
```

### Create virtual environment
```bash
uv venv
```

### Activate the virtual environment
```bash
source .venv/bin/activate
```

### Install Required Dependencies

#### Install fastmcp for the server
```bash
uv pip install fastmcp
```

#### Install boto3 for AWS integration
```bash
uv pip install boto3
```

#### Install any additional requirements if needed
```bash
uv pip install python-dotenv
```

### Configure AWS Credentials
Before running the application, ensure you have AWS credentials configured:

```bash
# Set up AWS credentials in ~/.aws/credentials or use environment variables
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=your_region
```

### Start the Server

#### Run the server with SSE transport on port 8080
```bash
fastmcp run weather-http-server.py:mcp --transport sse --port 8080 --host 0.0.0.0 --log-level debug
```

#### Run the Client
Open a new terminal window, activate the virtual environment, and run:

```bash
source .venv/bin/activate
python weatherClient.py http://localhost:8080
```

### 7. Testing the Application
Once both the server and client are running:

The client will prompt you for queries

Type your weather-related questions like 
- "what is the weather in New York" 
- "I'm travelling to Miami next week, what should I pack"
- "can I ski in Denver tomorrow" 
- "any severe weather alerts in Dallas" 

Type 'quit' to exit the application

