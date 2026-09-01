# Issue and PR description rules

Canonical sources (re-read if this file drifts):

- `.github/ISSUE_TEMPLATE/feature_request.yml`
- `.github/ISSUE_TEMPLATE/bug_report.yml`
- `.github/ISSUE_TEMPLATE/documentation.yml`
- `.github/PULL_REQUEST_TEMPLATE.md`

`blank_issues_enabled` is false — always use one of the three templates.

When creating via `gh`, use markdown `###` headings that match the form **labels**. GitHub stores issue-form answers that way.

---

## Feature issue (`[Feature]: …`)

Labels: `enhancement`, `needs-triage`

```markdown
### Problem Statement

<Why this is missing today. One or two sentences from the branch purpose.>

### Proposed Solution

<What this branch implements. Name registry ids, adapters, env vars.>

### Feature Category

<Exactly one option from the form:>
- New Virtual Try-On Provider
- New Image Generation Model
- New Video Generation Model
- New Dataset Support
- Preprocessing Enhancement
- Agent Enhancement
- API Improvement
- CLI Enhancement
- Demo / Web App
- Performance Improvement
- Documentation
- Other

### Suggested API / Interface

```python
# Example usage from the change, if applicable
```

### Alternatives Considered

<Other vendors, local vs API, or "None — first-party API.">

### Willing to Contribute

Yes, I'd like to implement this

### Additional Context

<Official docs URLs, related shipped models, Beijing-region / ADC notes.>
```

---

## Bug issue (`[Bug]: …`)

Labels: `bug`, `needs-triage`

```markdown
### Bug Description

<One paragraph.>

### Steps to Reproduce

1. …
2. …
3. See error

### Expected Behavior

<What should happen.>

### Actual Behavior

<What happens.>

### Component

<One option from bug_report.yml (Virtual Try-On, Image Generation, CLI, Documentation, Other, …).>

### Code Sample

```python
# Minimal repro if known
```

### Error Message / Traceback

```
<paste if present>
```

### Python Version

3.11.x

### Operating System

macOS / Linux / Windows (from the workspace)

### OpenTryOn Version

<`pip show opentryon` or commit hash>

### GPU Available

Yes / No / Not applicable

### Additional Context

<optional>
```

---

## Docs issue (`[Docs]: …`)

Labels: `documentation`, `needs-triage`

```markdown
### Issue Type

<Missing documentation | Incorrect / outdated information | Unclear explanation | Typo / grammar | Broken link | Missing code example | Other>

### Documentation Location

<file path or docs URL>

### Description

<What is wrong or missing.>

### Suggested Fix

<What the docs should say. This branch already does it if this is a docs PR.>

### Related Component

<Getting Started / Installation | Virtual Try-On APIs | Image Generation APIs | Video Generation APIs | Datasets Module | Preprocessing Functions | AI Agents | Demos / Examples | API Reference | Contributing Guide | Other>

### Willing to Contribute

Yes
```

---

## Pull request body

Copy the repo template. There is no GitHub Actions compliance job; keep the body short.

Always write `Fixes #<n>` or `Closes #<n>` in **Related Issue** so GitHub closes the issue on merge.

```markdown
## Description

<2–4 sentences: why this change exists and what lands for users (CLI `--model`, MCP tool, key).>

## Related Issue

Fixes #<n>

## Testing

<What was actually run, or that tests ran on a separate server. Do not invent results.>

## Additional Notes

<Auth caveats (Beijing key, ADC vs GEMINI_API_KEY). Restart MCP for Studio.>
```

---

## Issue reuse signals

Treat as the same change when any of these hold:

- Same registry id or upstream model id in the title/body
- Same bug symptom + component
- Same docs path
- Branch or commits already say `Fixes #n`

Do **not** reuse a leftover issue about a different model or a general backlog item (e.g. “add more VTON APIs”) unless the user points at that issue.
