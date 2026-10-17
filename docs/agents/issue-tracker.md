# Issue tracker: GitHub

Issues and specs live in GitHub Issues for `joshuahhn/roto_control`.
Use the `gh` CLI with `--repo joshuahhn/roto_control`.

## Operations

- Create: `gh issue create --repo joshuahhn/roto_control --title "..." --body-file <file>`.
- Read full body, labels and comments: `gh issue view <number> --repo joshuahhn/roto_control --json number,title,body,labels,comments`.
- List: `gh issue list --repo joshuahhn/roto_control --state open --json number,title,body,labels`.
- Comment: `gh issue comment <number> --repo joshuahhn/roto_control --body-file <file>`.
- Update body: `gh issue edit <number> --repo joshuahhn/roto_control --body-file <file>`.
- Labels: use `gh issue edit` with `--add-label` or `--remove-label` and the vocabulary in `triage-labels.md`.
- Close: record the requested resolution comment, then use `gh issue close`.

Use UTF-8 files with actual newlines for multiline bodies and comments.
“Publish” means create a GitHub issue; “fetch a ticket” means read its full body and comments.

## Parent and blocking relationships

Create children with `gh issue create --parent <parent>`, or link them using `gh issue edit <parent> --add-sub-issue <child>`.
Include the repository flag. If sub-issues are unavailable, put `Part of #<parent>` in the child body.

Publish blockers first. Fetch a blocker's numeric database ID with:
`gh api repos/joshuahhn/roto_control/issues/<blocker> --jq .id`.

Add a native blocking edge with:
`gh api --method POST repos/joshuahhn/roto_control/issues/<child>/dependencies/blocked_by -F issue_id=<blocker-db-id>`.

Use the database ID, not the issue number or node ID.
If native dependencies are unavailable, list issue references in a `Blocked by` section.
A ticket is on the frontier when every blocker is closed.

## Pull requests as a triage surface

**PRs as a request surface: no.**

## Wayfinding

The map is one issue labelled `wayfinder:map`; tickets are its sub-issues with `wayfinder:<type>` labels.
If sub-issues are unavailable, use a task list in the map and parent references in the children.
Choose an open, unassigned child with no open blockers.
Claim it using `gh issue edit <number> --repo joshuahhn/roto_control --add-assignee @me`.
Resolve by recording the answer, closing the child, and appending a context pointer to the map.
