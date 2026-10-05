"""Source connectors for the Teamwork Graph.

Each connector is responsible for:
  1. Fetching raw signals from a source (Slack, GitHub, …)
  2. Adding typed raw objects to the ActiveGraph graph
  3. Registering extraction behaviors that fire when those raw objects land

Canonical usage (all connectors):
  from activegraph import Graph
  from anywhere.connectors import make_teamwork_runtime
  from anywhere.connectors.slack import SlackConnector
  from anywhere.connectors.github import GitHubConnector

  graph = Graph()
  runtime = make_teamwork_runtime(graph, project_root="/path/to/project")
  slack = SlackConnector(project_root, graph, watched_channels=["#eng"])
  github = GitHubConnector(project_root, graph, watched_repos=["myrepo"])
  slack.sweep(); github.sweep()
  runtime.run_until_idle()

Single-connector usage (Slack only):
  from anywhere.connectors.slack import SlackConnector, make_teamwork_runtime
  ...  (Slack-only runtime, no GitHub behavior)
"""

from pathlib import Path

from activegraph import Graph, Runtime

from anywhere.connectors.slack import slack_thread_extractor, slack_canvas_extractor
from anywhere.connectors.github import github_pr_extractor


def make_teamwork_runtime(graph: Graph, project_root: str) -> Runtime:
    """Build a Runtime with all teamwork behaviors registered.

    Includes:
      - slack_thread_extractor  (fires on slack_thread_raw)
      - slack_canvas_extractor  (fires on slack_canvas_raw)
      - github_pr_extractor     (fires on github_pr_raw)

    The SQLite persistence file is written to <project_root>/.teamwork.sqlite.
    """
    db = str(Path(project_root) / ".teamwork.sqlite")
    return Runtime(
        graph,
        behaviors=[slack_thread_extractor, slack_canvas_extractor, github_pr_extractor],
        persist_to=db,
    )
