"""Tool registry — OpenAI-format schemas + executor factory for execute_with_tools()."""

from typing import Callable
from anywhere.tools import files, projects, slack_tools, github, search


TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file in the project directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path relative to project root"}
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file in the project directory. Creates parent directories if needed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path relative to project root"},
                    "content": {"type": "string", "description": "Content to write"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files in a directory within the project.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "Directory path relative to project root (default: '.')"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_issues",
            "description": "List all open issues in the project.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_issue",
            "description": "Read the details of a specific issue by ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "issue_id": {"type": "string", "description": "Issue ID (e.g. '0001')"},
                },
                "required": ["issue_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_issue",
            "description": "Create a new issue in the project.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "priority": {"type": "string", "enum": ["low", "medium", "high"], "description": "Default: medium"},
                },
                "required": ["title", "description"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "close_issue",
            "description": "Mark an issue as done with a resolution summary.",
            "parameters": {
                "type": "object",
                "properties": {
                    "issue_id": {"type": "string"},
                    "resolution": {"type": "string", "description": "What was done to resolve it"},
                },
                "required": ["issue_id", "resolution"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "slack_read_channel",
            "description": "Read recent messages from a Slack channel.",
            "parameters": {
                "type": "object",
                "properties": {
                    "channel": {"type": "string", "description": "Channel name (e.g. '#general') or channel ID"},
                    "limit": {"type": "integer", "description": "Number of messages to fetch (default: 20, max: 50)"},
                },
                "required": ["channel"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "slack_post",
            "description": "Post a message to a Slack channel.",
            "parameters": {
                "type": "object",
                "properties": {
                    "channel": {"type": "string"},
                    "text": {"type": "string"},
                },
                "required": ["channel", "text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "github_read_file",
            "description": "Read a file from a GitHub repository.",
            "parameters": {
                "type": "object",
                "properties": {
                    "repo": {"type": "string", "description": "Repo name or owner/repo"},
                    "path": {"type": "string", "description": "File path within the repo"},
                    "ref": {"type": "string", "description": "Branch or commit (default: main)"},
                },
                "required": ["repo", "path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "github_list_issues",
            "description": "List open issues in a GitHub repository.",
            "parameters": {
                "type": "object",
                "properties": {
                    "repo": {"type": "string", "description": "Repo name or owner/repo"},
                },
                "required": ["repo"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "github_list_my_repos",
            "description": "List all GitHub repositories owned by the configured user (VGBRO).",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "slack_search_messages",
            "description": "Search message content across the Slack workspace. Use to find discussions about a specific topic, account, or incident.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query (e.g. 'Acme renewal', 'sev1 outage')"},
                    "channel": {"type": "string", "description": "Optional: limit search to a specific channel name"},
                    "limit": {"type": "integer", "description": "Max results (default 20)"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for real-time information using Tavily. Use for current facts, prices, regulations, news, or anything that needs up-to-date data beyond the model's training cutoff.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "max_results": {"type": "integer", "description": "Number of results to return (default: 5, max: 10)"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "slack_search_channels",
            "description": "Find Slack channels whose name contains a keyword. Use to discover account-specific or topic-specific channels before reading them.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Keyword to search channel names for (e.g. 'acme', 'sev1', 'incident')"},
                    "limit": {"type": "integer", "description": "Max results (default 20)"},
                },
                "required": ["query"],
            },
        },
    },
]


def make_executor(repo_path: str) -> Callable[[str, dict], str]:
    """Return an executor function bound to repo_path for use with execute_with_tools()."""

    def executor(name: str, args: dict) -> str:
        if name == "read_file":
            return files.read_file(repo_path, args["path"])
        if name == "write_file":
            return files.write_file(repo_path, args["path"], args["content"])
        if name == "list_files":
            return files.list_files(repo_path, args.get("directory", "."))
        if name == "list_issues":
            return projects.list_issues(repo_path)
        if name == "read_issue":
            return projects.read_issue(repo_path, args["issue_id"])
        if name == "create_issue":
            return projects.create_issue(repo_path, args["title"], args["description"], args.get("priority", "medium"))
        if name == "close_issue":
            return projects.close_issue(repo_path, args["issue_id"], args["resolution"])
        if name == "slack_read_channel":
            return slack_tools.read_channel(args["channel"], args.get("limit", 20))
        if name == "slack_post":
            return slack_tools.post_message(args["channel"], args["text"])
        if name == "github_read_file":
            return github.read_file(args["repo"], args["path"], args.get("ref", "main"))
        if name == "github_list_issues":
            return github.list_issues(args["repo"])
        if name == "github_list_my_repos":
            return github.list_my_repos()
        if name == "slack_search_channels":
            return slack_tools.search_channels(args["query"], args.get("limit", 20))
        if name == "slack_search_messages":
            return slack_tools.search_messages(args["query"], args.get("channel"), args.get("limit", 20))
        if name == "web_search":
            return search.web_search(args["query"], args.get("max_results", 5))
        return f"Unknown tool: {name}"

    return executor
