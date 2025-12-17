# Start here your main.py code
import logging
import os
import threading
import time

import uvicorn
from agent_framework import HostedMCPTool, ToolMode
from agent_framework.azure import AzureAIAgentClient
from agent_framework.devui import serve
from azure.identity.aio import AzureCliCredential
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from models.issue_analyzer import IssueAnalyzer
from tools.github_tools import GitHubTools
from tools.time_per_issue_tools import TimePerIssueTools

load_dotenv()

# Crear aplicación FastAPI
app = FastAPI()

# Variable global para almacenar el agente
issue_analyzer_agent = None


class CheckDependenciesRequest(BaseModel):
    project_id: str
    description: str


@app.get("/")
async def hola_mundo():
    return {"mensaje": "Hola Mundo"}


@app.post("/check-dependencies")
async def check_dependencies(request: CheckDependenciesRequest):
    """Endpoint para analizar dependencias de un proyecto usando IssueAnalyzer"""
    global issue_analyzer_agent

    if issue_analyzer_agent is None:
        raise HTTPException(
            status_code=503, detail="Issue Analyzer agent not initialized yet")

    try:
        # Llamar al agente con la descripción del proyecto (await porque es async)
        prompt = f"Project ID: {request.project_id}\n\nAnalyze: {request.description}"
        response = await issue_analyzer_agent.run(prompt)

        # Devolver directamente la respuesta del agente
        return response
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error analyzing dependencies: {str(e)}")


def run_fastapi():
    """Función para ejecutar FastAPI en un thread separado"""
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="error")


def main():
    global issue_analyzer_agent

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    # Start FastAPI in a separate thread FIRST
    fastapi_thread = threading.Thread(target=run_fastapi, daemon=True)
    fastapi_thread.start()

    # Wait for FastAPI to start
    time.sleep(2)
    print("FastAPI started on http://0.0.0.0:8000")

    # Azure AI Agent settings
    settings = {
        "project_endpoint": os.environ["AZURE_AI_PROJECT_ENDPOINT"],
        "model_deployment_name": os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
        "credential": AzureCliCredential(),
    }

    # Instance TimerPerIssue tool
    time_per_issue_tools = TimePerIssueTools()

    # Instance GitHub tools
    github_tools = GitHubTools()

    # Create the issue analyzer agent (guardarlo en variable global)
    issue_analyzer_agent = AzureAIAgentClient(**settings).create_agent(
        instructions="""
            You are analyzing issues. 
            If the ask is a feature request the complexity should be 'NA'.
            If the issue is a bug, analyze the stack trace and provide the likely cause and complexity level.

            CRITICAL: You MUST use the provided tools for ALL calculations:
            1. First determine the complexity level
            2. Use the available tools to calculate time and cost estimates based on that complexity
            3. Never provide estimates without using the tools first

            Your response should contain only values obtained from the tool calls.
        """,
        name="IssueAnalyzerAgent",
        tool_choice=ToolMode.AUTO,
        tools=[time_per_issue_tools.calculate_time_based_on_complexity],
        response_format=IssueAnalyzer,
    )

    # Create the git hub agent (using REST API directly)
    github_agent = AzureAIAgentClient(**settings).create_agent(
        name="GitHubAgent",
        instructions=f"""
            You are a helpful assistant that can create issues on the user's GitHub repository based on the input provided.
            Use the create_github_issue tool to create issues.
            You work on this repository: {os.environ["GITHUB_PROJECT_REPO"]}
            
            When creating an issue:
            1. Use a clear and descriptive title
            2. Include all relevant details in the body
            3. Format the body with proper Markdown
        """,
        tools=[github_tools.create_github_issue],
    )

    # Create the GitHub MCP agent (using Model Context Protocol)
    # VERIFIED: This endpoint exists and provides 42 GitHub tools
    # Note: Microsoft docs show https://api.github.com/mcp (incorrect - 404)
    # Correct URL is https://api.githubcopilot.com/mcp/ (with trailing slash)
    github_mcp_agent = AzureAIAgentClient(**settings).create_agent(
        name="GitHubMCPAgent",
        instructions=f"""
            You are a helpful assistant that can create issues on the user's GitHub repository using the GitHub MCP tool.
            You have access to 42 GitHub tools including: create issues, PRs, search code/repos, manage branches, etc.
            You work on this repository: {os.environ["GITHUB_PROJECT_REPO"]}
        """,
        tools=HostedMCPTool(
            name="GitHub MCP",
            url="https://api.githubcopilot.com/mcp/",
            approval_mode="never_require",
            headers={
                "Authorization": f"Bearer {os.environ['GITHUB_MCP_PAT']}",
            },
        ),
    )

    # Create the Microsoft Learn MCP agent (using official Microsoft MCP server)
    mslearn_mcp_agent = AzureAIAgentClient(**settings).create_agent(
        name="MSLearnMCPAgent",
        instructions="""
            You answer questions by searching Microsoft Learn content only.
            Use the Microsoft Learn MCP tool to find documentation and technical resources.
            Provide clear and accurate responses based on official Microsoft documentation.
        """,
        tools=HostedMCPTool(
            name="Microsoft Learn MCP",
            url="https://learn.microsoft.com/api/mcp",
            approval_mode="never_require",
        ),
    )

    # Start the DevUI server (blocking)
    serve(entities=[issue_analyzer_agent, github_agent, github_mcp_agent, mslearn_mcp_agent], port=8090,
          auto_open=True, tracing_enabled=True)


if __name__ == "__main__":
    main()
