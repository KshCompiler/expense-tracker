---
name: readme-sync
description: Update README.md to reflect the current state of the project. Trigger this automatically — without being asked by name — whenever the user asks to commit, push, or commit-and-push changes (e.g. "commit this", "push it", "commit and push"), and also whenever Claude itself is about to run `git commit` or `git push` on the user's behalf. Also runs on explicit manual invocation ("/readme-sync", "update the readme"). Reviews the codebase, updates the top-of-file description of what the project does plus the Features / Tech Stack / Project Structure / Getting Started sections, and applies the edit directly (no confirmation gate) since README drift is low-risk to fix.
---

# README Sync

Keeps `README.md` accurate as the project evolves, by diffing what it currently says against what the codebase currently does.

## When this triggers

Trigger automatically, without the user needing to name this skill, whenever:
- The user asks to commit, push, or commit-and-push (e.g. "commit this", "push it", "commit and push", "ship this").
- Claude is about to run `git commit` and/or `git push` for the user for any other reason (e.g. as the last step of a task the user asked for).

Run this skill's workflow *before* the commit/push executes, so any README changes it makes land in the same commit/push rather than as an afterthought.

Also invoke on explicit manual request ("/readme-sync", "update the readme", "sync the readme").

Note the scope: this only fires inside a live Claude Code conversation, when Claude itself is the one running (or being asked to run) the git command. It cannot react to a bare `git commit`/`git push` typed directly in a terminal outside a Claude Code session — that would require a git hook, which is separate machinery from skills.

Skip the update if a check against the codebase (see Workflow below) turns up no drift — don't touch the file just because a commit/push is happening.

## Workflow

1. **Establish what's changed.**
   - Run `git log --oneline -15` and `git diff --stat HEAD~5` (adjust range as appropriate) to see recent work.
   - Check `.claude/specs/` for any spec files newer than what's reflected in the README's Features list.
   - Skim `backend/app/routers/` and `frontend/src/pages/` for the current set of features/routes.
   - Check `backend/requirements.txt` and `frontend/package.json` for the current dependency set.

2. **Read `README.md` in full** before editing — don't assume its structure from memory.

3. **Update, section by section, only what's stale:**
   - **Top description line** — one sentence stating what the project does; keep it current if the scope changed.
   - **Features** — add/remove/reword bullets to match what's actually implemented. Don't describe planned or half-finished work as shipped.
   - **Tech Stack** — reflect actual dependencies in use, not aspirational ones.
   - **Project Structure** — update the file tree comments if routers/components/pages were added, removed, or renamed.
   - **Getting Started / Testing** — update commands, ports, or env vars if they changed.
   - **Deployment Notes** — update if deployment-relevant config changed.
   - Leave sections untouched if they're still accurate — this is a sync, not a rewrite.

4. **Apply the edit directly** with the file-editing tool (no approval gate — README drift is low-stakes and easily reverted via git).

5. **Report a short summary** of what sections changed and why (one line per section touched) — no other narration.

## Notes

- Never invent features that don't exist in the codebase — every Features bullet must trace to actual code (a router, a page, a component).
- Don't add a changelog, "recently added" callouts, or history framing (e.g. "migrated from X") — the README describes current state only.
- Preserve existing heading structure, tone, and formatting conventions already in the file.
- If the README is missing a section that now clearly applies (e.g. a new major feature area with its own setup step), add it in a sensible place and say so in the summary.
