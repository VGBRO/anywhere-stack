"""Source connectors for the Teamwork Graph.

Each connector is responsible for:
  1. Fetching raw signals from a source (Slack, GitHub, Google Meet, …)
  2. Adding typed raw objects to the ActiveGraph graph
  3. Registering extraction behaviors that fire when those raw objects land

Canonical usage (all connectors):
  from activegraph import Graph
  from anywhere.connectors import make_teamwork_runtime
  from anywhere.connectors.slack import SlackConnector
  from anywhere.connectors.github import GitHubConnector
  from anywhere.connectors.googlemeet import GoogleMeetConnector

  graph = Graph()
  runtime = make_teamwork_runtime(graph, project_root="/path/to/project")
  slack = SlackConnector(project_root, graph, watched_channels=["#eng"])
  github = GitHubConnector(project_root, graph, watched_repos=["myrepo"])
  meet = GoogleMeetConnector(project_root, graph, transcripts_dir="/path/to/vtts")
  slack.sweep(); github.sweep(); meet.sweep()
  runtime.run_until_idle()

Single-connector usage (Slack only):
  from anywhere.connectors.slack import SlackConnector, make_teamwork_runtime
  ...  (Slack-only runtime, no GitHub/Meet behaviors)
"""

from pathlib import Path

from activegraph import Graph, Runtime

from anywhere.connectors.slack import slack_thread_extractor, slack_canvas_extractor
from anywhere.connectors.github import github_pr_extractor
from anywhere.connectors.googlemeet import meeting_transcript_extractor


def make_teamwork_runtime(graph: Graph, project_root: str) -> Runtime:
    """Build a Runtime with all teamwork behaviors registered.

    Includes:
      - slack_thread_extractor       (fires on slack_thread_raw)
      - slack_canvas_extractor       (fires on slack_canvas_raw)
      - github_pr_extractor          (fires on github_pr_raw)
      - meeting_transcript_extractor (fires on meeting_transcript_raw)

    The SQLite persistence file is written to <project_root>/.teamwork.sqlite.
    """
    db = str(Path(project_root) / ".teamwork.sqlite")
    return Runtime(
        graph,
        behaviors=[
            slack_thread_extractor,
            slack_canvas_extractor,
            github_pr_extractor,
            meeting_transcript_extractor,
        ],
        persist_to=db,
    )
