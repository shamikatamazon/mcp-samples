from strands import Agent, tool
import os
from strands.telemetry.tracer import get_tracer
from strands.models import BedrockModel

# Create an agent with default settings

os.environ["STRANDS_OTEL_ENABLE_CONSOLE_EXPORT"] = "false"

tracer = get_tracer(
    service_name="my-agent-service",
    otlp_endpoint="http://localhost:4318",
    #otlp_headers={"Authorization": "Bearer TOKEN"},
    #enable_console_export=False  # Helpful for development
)

nova_agent_model = BedrockModel(
    model_id="us.amazon.nova-lite-v1:0",
    temperature=0,
    max_tokens=1000,
    top_p=1,
    streaming=False,
)


@tool
def calculator(number1: int, number2:int, operation:str) -> str:
    """A simple calculator tool. The tool takes as input 2 numbers and a operation, like 2,2, "add" and the response is 4 
    operation can only be one of add/subtract/multiply/divide"""

    if operation == "add":
        return str(number1 + number2)
    elif operation == "subtract":
        return str(number1 - number2)
    elif operation == "multiply":
        return str(number1 * number2)
    elif operation == "divide":
        return str(number1 / number2)


CALC_SYSTEM_PROMPT = "you are a calculator, specializing in calling the appropriate tools to perform mathematical functions. always call a tool for math operations."

calc_agent = Agent(system_prompt=CALC_SYSTEM_PROMPT, 
    tools=[calculator],
    model = nova_agent_model)

print(calc_agent.model.config)

# Ask the agent a question
result = calc_agent("Add 245 and 25645")

print(f"\nTotal tokens: {result.metrics.accumulated_usage['totalTokens']}")
print(f"\nExecution time: {sum(result.metrics.cycle_durations):.2f} seconds")
print(f"\nTools used: {list(result.metrics.tool_metrics.keys())}")