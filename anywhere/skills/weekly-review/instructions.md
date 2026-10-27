# Weekly Review Skill

You produce a sharp weekly digest: what shipped, what's stuck, what needs attention this week.

## Process
1. Use `list_files` to enumerate all local projects
2. For each project: `read_file` on `state.md`, `brief.md`, and `list_issues` for open items
3. Use `github_list_my_repos` → for repos with open issues, call `github_list_issues`
4. Use `slack_search_channels` for "anywhere" or "weekly" to find a digest channel
5. Write the digest to `reviews/week-<YYYY-MM-DD>.md`
6. Post a condensed version to the digest Slack channel

## Digest Structure
```
# Weekly Digest — [Date]

## Shipped This Week
- [project]: [what was completed]

## In Progress
- [project]: [what's actively being worked, key open issues]

## Blocked / Needs Attention
- [project]: [blocker description, what's needed to unblock]

## GitHub Activity
- [repo]: [N open issues, notable ones]

## This Week's Focus
[Top 3 priorities for the coming week, ranked]
```

## Rules
- Only include projects with meaningful activity — skip empty ones
- GitHub issues with no internal match = surface them, don't auto-create (that's the heartbeat's job)
- Post to Slack: condensed to 3-5 bullet points, link to full digest file
- Be honest about what's stuck — don't spin a blocked item as "in progress"
