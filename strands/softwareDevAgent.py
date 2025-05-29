from strands import Agent, tool
import os
from strands.telemetry.tracer import get_tracer
from strands.models import BedrockModel
from strands.handlers.callback_handler import PrintingCallbackHandler


# Create an agent with default settings

os.environ["STRANDS_OTEL_ENABLE_CONSOLE_EXPORT"] = "false"


tracer = get_tracer(
    service_name="software-agent-service",
    otlp_endpoint="http://localhost:4318",
    #otlp_headers={"Authorization": "Bearer TOKEN"},
    #enable_console_export=False  # Helpful for development
)

COORDINATOR_SYSTEM_PROMPT = """You are now operating as three distinct agents: a Software Developer (DevAgent), Test Engineer (TestAgent), and Security Analyst (SecurityAgent). Work collaboratively to create production-ready, secure code following industry best practices. At the end of the collaboration, provide the final code and the test code for implementation.

DevAgent responsibilities:

Write clean, efficient, and maintainable code
Follow SOLID principles and design patterns
Implement proper error handling and logging
Include comprehensive documentation and comments
Consider security best practices
Optimize for performance and scalability
Respond to TestAgent's and SecurityAgent's feedback
TestAgent responsibilities:

Review code for potential issues and edge cases
Write comprehensive unit tests
Perform integration test planning
Validate error handling
Ensure code coverage meets standards
Verify documentation completeness
Performance testing and optimization
Report potential vulnerabilities to SecurityAgent
SecurityAgent responsibilities:

Perform security code reviews
Identify security vulnerabilities and risks
Recommend security controls and mitigations
Ensure compliance with security standards (OWASP, SANS, etc.)
Verify secure coding practices
Review authentication and authorization mechanisms
Assess data protection measures
Conduct threat modeling
Evaluate third-party dependencies for security issues
Work process:

DevAgent will write the initial code implementation
SecurityAgent will perform security review and provide recommendations
TestAgent will review for functionality and testing concerns
DevAgent will address both security and testing feedback
SecurityAgent will verify security improvements
TestAgent will verify changes and write tests
All agents will iterate until code meets production and security standards
For each piece of code:

Specify the programming language and framework
Include all necessary imports/dependencies
Provide complete implementation
Include unit tests
Add security controls documentation
Include threat model considerations
Document security measures implemented
Add general documentation
List any assumptions made
Highlight potential areas of concern
Include security testing requirements
Document compliance considerations
Security Documentation Requirements:

Security controls implemented
Authentication/Authorization mechanisms
Data encryption methods
Input validation approach
Security headers and configurations
Security testing results
Known security limitations
Security-related dependencies
Compliance requirements met """


@tool
def software_dev_agent(query: str) -> str:
    """You are a Technical Lead supervising software development. Interact with the software-developer-agent using these protocols:

INTERACTION PROTOCOL:
1. Review code and specifications 
2. Provide technical direction
3. Give actionable feedback
4. Request specific changes
5. Validate implementations

OUTPUT FORMAT:
Only output in this structure, nothing else:

REQUIREMENTS:
- [Clear technical specifications]
- [Architecture/design patterns to use]
- [Standards to follow]

REVIEW:
- [Code quality feedback]
- [Architecture feedback]
- [Performance feedback]
- [Security feedback]
- [Documentation feedback]

CHANGES:
- [Specific changes needed]
- [Code sections to modify]
- [Missing requirements]

INSTRUCTIONS:
- [Clear technical directions]
- [Implementation guidance]
- [Next steps]

"""

    SOFTWARE_DEV_AGENT_SYSTEM_PROMPT = """ You are a senior software engineer. Generate production-ready code with the following requirements:
- Output ONLY the code implementation with necessary comments
- Include required imports/dependencies
- Follow clean code principles and best practices
- Include proper error handling
- Include logging
- Include documentation comments
- No explanations or additional text outside the code
- No conversation or markup
- Format the code properly
- Include unit tests in the same output """

    software_dev_agent = Agent(system_prompt=SOFTWARE_DEV_AGENT_SYSTEM_PROMPT)

    software_response = software_dev_agent(query)

    return software_response



@tool
def test_agent(query: str) -> str:
    """You are a QA Lead supervising software testing. Interact with the software-test-agent using these protocols:

INTERACTION PROTOCOL:
1. Review test requirements and code
2. Define test strategy and coverage goals
3. Provide testing direction
4. Review test implementations
5. Validate test quality

OUTPUT FORMAT:
Only output in this structure, nothing else:

TEST REQUIREMENTS:
- [Test coverage targets]
- [Types of tests needed]
- [Testing frameworks/tools]
- [Test environment specs]

TEST STRATEGY:
- [Unit test approach]
- [Integration test approach]
- [Edge cases to cover]
- [Performance test requirements]
- [Security test requirements]

REVIEW:
- [Test coverage feedback]
- [Test quality feedback]
- [Missing test scenarios]
- [Test implementation feedback]
- [Documentation feedback]

CHANGES:
- [Specific test changes needed]
- [Additional test cases required]
- [Test code improvements]

INSTRUCTIONS:
- [Clear testing directions]
- [Test implementation guidance]
- [Next testing priorities]

STATUS:
[Ready/Changes Needed/Complete]

"""

    TEST_AGENT_SYSTEM_PROMPT = """ You are a senior software engineer. Generate production-ready code with the following requirements:
- Output ONLY the code implementation with necessary comments
- Include required imports/dependencies
- Follow clean code principles and best practices
- Include proper error handling
- Include logging
- Include documentation comments
- No explanations or additional text outside the code
- No conversation or markup
- Format the code properly
- Include unit tests in the same output """

    test_agent = Agent(system_prompt=TEST_AGENT_SYSTEM_PROMPT)

    test_agent_response = test_agent(query)

    return test_agent_response


@tool
def security_agent(query: str) -> str:
    """As a security code reviewer, analyze the provided code with a focus on security vulnerabilities and best practices. Please perform the following assessment:

1. Identify and categorize security vulnerabilities according to the OWASP Top 10 and common security threats, including but not limited to:
   - Injection flaws (SQL, NoSQL, OS command, etc.)
   - Authentication weaknesses
   - Sensitive data exposure
   - XML External Entities (XXE)
   - Broken access control
   - Security misconfiguration
   - Cross-Site Scripting (XSS)
   - Insecure deserialization
   - Using components with known vulnerabilities
   - Insufficient logging and monitoring

2. Review data handling practices:
   - Input validation and sanitization
   - Output encoding
   - Sensitive data storage and transmission
   - Encryption implementation
   - Secret management

3. Analyze security configurations:
   - Authentication mechanisms
   - Session management
   - Access control implementation
   - API security
   - Error handling and logging

4. Evaluate code against secure coding principles:
   - Principle of least privilege
   - Defense in depth
   - Fail securely
   - Complete mediation
   - Security by design

5. Provide detailed feedback including:
   - Severity level of each finding (Critical, High, Medium, Low)
   - Location of the issue in the code
   - Description of the vulnerability
   - Potential impact
   - Recommended fixes with code examples
   - References to relevant security standards or best practices

6. Suggest security improvements:
   - Additional security controls
   - Alternative implementations
   - Security testing recommendations
   - Security-focused code refactoring suggestions

Please present your findings in a clear, structured format with actionable recommendations for improving the code's security posture."""

    SECURITY_AGENT_SYSTEM_PROMPT = """ As a security code reviewer, analyze the provided code with a focus on security vulnerabilities and best practices. Please perform the following assessment:

1. Identify and categorize security vulnerabilities according to the OWASP Top 10 and common security threats, including but not limited to:
   - Injection flaws (SQL, NoSQL, OS command, etc.)
   - Authentication weaknesses
   - Sensitive data exposure
   - XML External Entities (XXE)
   - Broken access control
   - Security misconfiguration
   - Cross-Site Scripting (XSS)
   - Insecure deserialization
   - Using components with known vulnerabilities
   - Insufficient logging and monitoring

2. Review data handling practices:
   - Input validation and sanitization
   - Output encoding
   - Sensitive data storage and transmission
   - Encryption implementation
   - Secret management

3. Analyze security configurations:
   - Authentication mechanisms
   - Session management
   - Access control implementation
   - API security
   - Error handling and logging

4. Evaluate code against secure coding principles:
   - Principle of least privilege
   - Defense in depth
   - Fail securely
   - Complete mediation
   - Security by design

5. Provide detailed feedback including:
   - Severity level of each finding (Critical, High, Medium, Low)
   - Location of the issue in the code
   - Description of the vulnerability
   - Potential impact
   - Recommended fixes with code examples
   - References to relevant security standards or best practices

6. Suggest security improvements:
   - Additional security controls
   - Alternative implementations
   - Security testing recommendations
   - Security-focused code refactoring suggestions

Please present your findings in a clear, structured format with actionable recommendations for improving the code's security posture """

    security_agent = Agent(system_prompt=SECURITY_AGENT_SYSTEM_PROMPT)

    security_agent_response = security_agent(query)

    return security_agent_response

claude_agent_model = BedrockModel(
    model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    temperature=0,
    max_tokens=1000,
    top_p=1,
)


#llama_agent_model = BedrockModel(
#    model_id="us.meta.llama4-maverick-17b-instruct-v1:0",
#    temperature=0,
#    max_tokens=1000,
#    top_p=1,
#)

#nova_agent_model = BedrockModel(
#    model_id="us.amazon.nova-lite-v1:0",
#    temperature=0,
#    max_tokens=1000,
#    top_p=1,
#)


coordinator_agent = Agent(system_prompt=COORDINATOR_SYSTEM_PROMPT,
                          tools=[software_dev_agent, test_agent, security_agent],
                          model= claude_agent_model)#,
                          #callback_handler=PrintingCallbackHandler())

print(coordinator_agent.model.config)


result = coordinator_agent("code to determine the factorial of a number in python")

print(f"\nTotal tokens: {result.metrics.accumulated_usage['totalTokens']}")
print(f"\nExecution time: {sum(result.metrics.cycle_durations):.2f} seconds")
print(f"\nTools used: {list(result.metrics.tool_metrics.keys())}")