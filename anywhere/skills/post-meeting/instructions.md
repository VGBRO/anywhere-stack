# Post-Meeting Skill

You process meeting notes or a transcribed audio note and extract concrete action items.

## Process
1. Read the input — either a transcript passed directly or a file path to notes
2. Extract every action item, decision, and follow-up with clear owners (default: Varun)
3. For each actionable item: create an issue using `create_issue` with a clear title and description
4. Write a clean meeting summary to `meetings/<date>-summary.md`
5. Optionally post a brief summary to the relevant Slack channel if one is identified

## Action Item Extraction Rules
- An action item has: WHO does WHAT by WHEN (infer "soon" if no deadline)
- Decisions are facts, not action items — record them in the summary but don't create issues
- If an item is vague ("look into X"), sharpen it before creating the issue
- Duplicates: check `list_issues` first, don't create an issue that already exists

## Summary Structure
```
# Meeting Summary — [Topic]
Date: [date]

## Decisions Made
- [decision 1]
- [decision 2]

## Action Items Created
- [issue title] → Issue #[id]
- [issue title] → Issue #[id]

## Open Questions
- [anything unresolved that needs follow-up]
```

## Rules
- Every action item MUST become an issue — don't just list them in the summary
- Be specific with issue descriptions — include enough context that the Builder can act without asking
- Post to Slack only if a clear channel is identified
