import asyncio
import os
from agent_framework.azure import AzureAIAgentClient
from agent_framework import ChatAgent
from azure.identity.aio import AzureCliCredential
from dotenv import load_dotenv
from models.issue_analyzer import IssueAnalyzer

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
            instructions="You are analyzing issues.",
            name="IssueAnalyzerAgent",
            response_format=IssueAnalyzer
        )

        result = await agent.run("""
                Traceback (most recent call last):
                    File "<string>", line 38, in <module>
                        main_application()                    ← Entry point
                    File "<string>", line 30, in main_application
                        results = process_data_batch(test_data)  ← Calls processor
                    File "<string>", line 13, in process_data_batch
                        avg = calculate_average(batch)        ← Calls calculator
                    File "<string>", line 5, in calculate_average
                        return total / count                  ← ERROR HERE
                            ~~~~~~^~~~~~~
                    ZeroDivisionError: division by zero
                                 """)
        print(result.text)


asyncio.run(main())
