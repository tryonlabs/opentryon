---
name: deploy-docs
description: >-
  Builds the OpenTryOn Docusaurus site in docs/, commits and pushes to the docs
  branch, and deploys GitHub Pages (gh-pages). Use when the user asks to build
  docs, deploy documentation, publish GitHub Pages, npm run deploy, or run
  /deploy-docs. Commit the code to the docs branch and do not commit to the main
  branch. This skill will not create a pull request to merge the doc branch to
  the main branch.
---

# Deploy docs (GitHub Pages)

Publish the Docusaurus site from `docs/` to **https://tryonlabs.github.io/opentryon/**.

GitHub Pages is served from the **`gh-pages`** branch (`docs/package.json` `npm run deploy` → `docusaurus build && gh-pages -d build`). The Actions workflow `.github/workflows/deploy-docs.yml` is disabled.

Commit the code to the docs branch and do not commit to the main branch. This skill will not create a pull request to merge the doc branch to the main branch.

Repo root: OpenTryOn (`opentryon/`). In a multi-root workspace, run every command with `working_directory` `/Users/apple/tryonlabs/repos/opentryon` (or `git -C` that path).

## Constraints (do not skip)

| Allowed | Forbidden |
|---|---|
| Commit **only** on **`docs`** | Commit on `main`, `master`, or any other branch |
| Push **`docs`** (source) and **`gh-pages`** (Pages, via `gh-pages` CLI) | Push `main` / `master` |
| `npm run build` then `npx gh-pages -d build` | `gh pr create`, `gh pr edit`, any PR from `docs` → `main` |
| | Force-push unless the user explicitly asked **and** the target is not `main`/`master` |
| | Amend, skip hooks, edit `git config` |

`gh-pages -d build` creates a commit **on `gh-pages` only**. That is the Pages deploy, not a source commit on `main`.

## Workflow

```
Task Progress:
- [ ] 1. Confirm repo + move work onto docs (never commit on main)
- [ ] 2. Install + build docs/
- [ ] 3. Commit on docs (if there is something to commit)
- [ ] 4. Push origin docs
- [ ] 5. Deploy to gh-pages
- [ ] 6. Return URLs — no PR
```

### 1. Confirm repo + land on `docs`

```bash
git rev-parse --show-toplevel
git rev-parse --abbrev-ref HEAD
git status -sb
```

**Stop if** the toplevel is not the `opentryon` repo.

If HEAD is `main` or `master`: **do not commit**. Switch to `docs` first, bringing uncommitted work along:

```bash
git stash push -u -m "deploy-docs"
git checkout docs 2>/dev/null || git checkout -b docs
git stash pop
```

If `docs` does not exist locally but exists on origin: `git checkout -b docs origin/docs` (then stash pop).

If HEAD is already `docs`, continue.

If HEAD is some other feature branch: stop and say the skill only commits on `docs` — do not commit that feature branch and do not commit `main`.

### 2. Build

From `docs/` (Node ≥ 18):

```bash
npm install
npm run build
```

`onBrokenLinks` is `throw`. If the build fails, fix the reported links (or stop and report). Do not deploy a failed build.

Built files: `docs/build/`. Site path: `baseUrl` `/opentryon/`. Do not commit `docs/build/` or `docs/node_modules/` (they are gitignored).

### 3. Commit on `docs` only

Confirm `git rev-parse --abbrev-ref HEAD` is `docs`. If it is `main`/`master`, go back to step 1 — never `git commit` there.

Then, in parallel:

```bash
git status
git diff
git log -5 --oneline
```

Stage documentation and skill files that belong in this deploy (typically `docs/`, `README.md`, `mcp-server/README.md`, `.cursor/skills/deploy-docs/` as relevant). Do **not** stage secrets (`.env`, credentials).

If there is nothing to commit, skip to step 4.

Commit with a HEREDOC (no `-i`, no `--amend`, no `--no-verify`):

```bash
git commit -m "$(cat <<'EOF'
Short why-focused message for the docs update.

EOF
)"
```

### 4. Push `docs`

```bash
git push -u origin docs
```

Needs network (`required_permissions: ["all"]`). Do **not** push `main`.

### 5. Deploy (push `gh-pages` only)

From `docs/`:

```bash
npx gh-pages -d build
```

(`npm run deploy` rebuilds then runs `gh-pages -d build`. Prefer `npx gh-pages -d build` after a successful step 2.)

### 6. Reply

Return:

1. Build result (ok / failed)
2. Commit on **`docs`** (hash / that there was nothing to commit)
3. That **`docs`** was pushed
4. That **`gh-pages`** was updated (or the error)
5. That **no PR** was opened to merge `docs` into `main`
6. Live URL: https://tryonlabs.github.io/opentryon/ (allow a few minutes for Pages)

## Do not

- Commit the code to the main branch
- Create a pull request to merge the docs branch to the main branch
- Push `main` / `master`
- Force-push `main` / `master`
- Edit `git config`
- Treat Actions `deploy-docs.yml` as the deploy path
- Put secrets in the reply
