---
name: open-issue-pr
description: >-
  Inspects commits on the current branch, creates or reuses a GitHub issue
  for that change, and opens a pull request to main using the repo issue and
  PR templates. Use when the user asks to create an issue,
  open a PR, ship the branch, write issue/PR descriptions, or run
  /open-issue-pr.
---

# Open issue + PR (current branch → main)

OpenTryOn workflow: **issue first** ([CONTRIBUTING.md](../../../CONTRIBUTING.md)), then a PR into **`main`**. Issue bodies follow `.github/ISSUE_TEMPLATE/`. PR bodies follow `.github/PULL_REQUEST_TEMPLATE.md` (short description; no GitHub Actions compliance job — tests run outside GitHub).

Read [templates.md](templates.md) before writing bodies. Re-read the live `.github` files if they differ from that snapshot.

Do **not** commit, amend, force-push, or skip hooks unless the user explicitly asked. Do **not** create a second issue for the same change.

## Workflow

```
Task Progress:
- [ ] 1. Inspect branch vs main
- [ ] 2. Find an existing issue for this change
- [ ] 3. Create an issue only if none exists
- [ ] 4. Push the branch if needed
- [ ] 5. Open (or update) a PR to main
- [ ] 6. Return issue URL + PR URL
```

### 1. Inspect the branch

Run these in parallel with the Shell tool (repo root):

```bash
git status -sb
git rev-parse --abbrev-ref HEAD
git rev-parse --abbrev-ref @{upstream} 2>/dev/null || true
git log --oneline main...HEAD
git diff main...HEAD --stat
git log -1 --format='%s%n%n%b'
```

Also `git log main...HEAD` (full subjects) and a skim of `git diff main...HEAD` so the issue/PR cover **every commit**, not only HEAD.

**Stop if:**

| Situation | Action |
|---|---|
| Current branch is `main` / `master` | Ask for a feature branch. Do not open a PR from main. |
| `main...HEAD` is empty | Nothing to ship. If the user still wants an issue, write it from uncommitted work and **do not** open a PR until there are commits. |
| Uncommitted or unstaged files exist | Warn. The PR will not include them. Do not commit unless the user asked. |
| `gh` is missing or not authenticated | Stop and say so. |

Default base branch is **`main`**.

### 2. Find an existing issue (do not duplicate)

Search in this order. Use the **first clear match**.

1. Branch name: `#123`, `issue-123`, `/123-`.
2. Commit messages: `Fixes #N`, `Closes #N`, `Resolves #N`, bare `#N`.
3. Existing PR on this branch: `gh pr view --json number,url,body,state`.
4. GitHub search (open first, then recently closed):

```bash
gh issue list --state open --limit 50 --search "KEYWORD"
gh issue list --state all --limit 20 --search "KEYWORD in:title"
```

`KEYWORD`s come from the change: registry ids (`outfitanyone-plus`), adapter names, short commit subjects. Match only when the issue is clearly the **same change** (same model/bug/docs page), not a vague related topic.

If a match exists: **reuse that issue number**. Do not create another.

### 3. Create an issue only if none exists

The skill **automatically creates** an issue for the current change when step 2 finds none.

Pick a template from the commits:

| Change | Template | Title prefix | Labels |
|---|---|---|---|
| New feature / model / adapter | `feature_request.yml` | `[Feature]: ` | `enhancement`, `needs-triage` |
| Bug fix | `bug_report.yml` | `[Bug]: ` | `bug`, `needs-triage` |
| Docs-only | `documentation.yml` | `[Docs]: ` | `documentation`, `needs-triage` |

Write the body from [templates.md](templates.md) (GitHub form headings). Fill required fields from the branch diff. For features, set **Willing to Contribute** to `Yes, I'd like to implement this`.

```bash
gh issue create --title "TITLE" --label "LABELS" --body "$(cat <<'EOF'
BODY
EOF
)"
```

Record the new issue number. Do not `@` maintainers.

### 4. Push the branch

If the branch has no upstream, or is ahead of origin:

```bash
git push -u origin HEAD
```

Needs network (`all` / `full_network`). Never `--force` unless the user explicitly requested it **and** the branch is not `main`.

### 5. Open a PR to `main`

If `gh pr view` already shows an open PR for this branch into `main`, **update** its body (`gh pr edit`) if Description / Related Issue are missing. Do not open a second PR.

Otherwise:

```bash
gh pr create --base main --title "TITLE" --body "$(cat <<'EOF'
BODY
EOF
)"
```

PR body follows `.github/PULL_REQUEST_TEMPLATE.md` (see [templates.md](templates.md)):

- `## Description` with real text
- `## Related Issue` with `Fixes #N` or `Closes #N`
- `## Testing` with what was actually run (or that tests ran on a separate server)

Title: short, from the commits (what changed). Not a dump of file names.

### 6. Reply to the user

Return:

1. Whether the issue was **reused** or **created**
2. Issue URL
3. PR URL
4. One line if uncommitted files were left out

## Do not

- Create an issue when one already covers this change
- Open a PR to a branch other than `main` unless the user named another base
- Invent test results — only report what was actually run
- Put secrets (`.env`, keys) in issue or PR text
- Force-push, amend, or commit unless asked
