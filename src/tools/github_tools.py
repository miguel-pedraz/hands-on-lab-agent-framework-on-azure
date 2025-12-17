import os
from typing import Annotated

import requests


class GitHubTools:
    """Tools for interacting with GitHub API directly."""

    def __init__(self, pat_token: str = None, repo: str = None):
        self.pat_token = pat_token or os.environ.get("GITHUB_MCP_PAT")
        self.repo = repo or os.environ.get("GITHUB_PROJECT_REPO")
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"Bearer {self.pat_token}",
            "Accept": "application/vnd.github.v3+json",
        }

    def create_github_issue(
        self,
        title: Annotated[str, "The title of the GitHub issue"],
        body: Annotated[str, "The body/description of the GitHub issue"],
        labels: Annotated[list[str], "Optional list of labels"] = None
    ) -> str:
        """
        Create a new issue in the GitHub repository.

        Args:
            title: The issue title
            body: The issue description/body
            labels: Optional list of labels to apply

        Returns:
            A message indicating success or failure with the issue URL
        """
        url = f"{self.base_url}/repos/{self.repo}/issues"

        payload = {
            "title": title,
            "body": body,
        }

        if labels:
            payload["labels"] = labels

        try:
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()

            issue_data = response.json()
            issue_number = issue_data.get("number")
            issue_url = issue_data.get("html_url")

            return f"✅ Successfully created issue #{issue_number}: {issue_url}"

        except requests.exceptions.HTTPError as e:
            return f"❌ Failed to create issue: {e.response.status_code} - {e.response.text}"
        except Exception as e:
            return f"❌ Error creating issue: {str(e)}"
