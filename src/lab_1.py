import asyncio
import os
from agent_framework.azure import AzureAIAgentClient
from agent_framework import ChatAgent
from azure.identity.aio import AzureCliCredential
from dotenv import load_dotenv

load_dotenv()


async def main():
    async with (
        AzureAIAgentClient(
            project_endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            model_deployment_name=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
            async_credential=AzureCliCredential(),
        ) as client,
    ):
        agent = ChatAgent(
            chat_client=client,
            instructions="You are good at telling jokes.",
            name="Joker",
        )

        result = await agent.run("Tell me a joke about a pirate.")
        print(result.text)


asyncio.run(main())
