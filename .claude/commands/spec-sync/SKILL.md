---
name: spec-sync
description: Keep the project's spec file in sync whenever the user proposes or discusses a change to requirements, scope, features, or behavior. Use this skill any time the user suggests, requests, or describes a change to "Claude," the project, a feature, or how something should work — even informally (e.g. "let's also support X", "actually can we change Y to Z", "I want to add..."). Looks for the spec file under .claude/specs/, proposes a precise diff reflecting the discussed change, and always waits for explicit user approval (yes/no) before writing anything to disk. Do not edit the spec file without first showing the diff and getting confirmation.
---

# Spec Sync

Keeps a project's markdown spec file (PRD/requirements doc) accurate as the user proposes changes in conversation, without ever writing to the file unannounced.

## When this triggers

Use this skill whenever the user describes a change, addition, removal, or correction to how a project/feature/"Claude" should behave or what it should do — including casual phrasing like "let's change...", "can we also...", "actually I want...", "remove the part about...", "update X to Y". It does not need to be phrased as an explicit request to "update the spec."

Do NOT trigger for purely exploratory questions ("what do you think about X?") where the user hasn't actually decided on a change yet.

## Workflow

1. **Locate the spec file.**
   - Look under `.claude/specs/` in the current project directory.
   - If there are multiple `.md` files there, ask the user which one applies (unless it's obvious from context — e.g. only one file, or the filename matches the topic being discussed).
   - If `.claude/specs/` doesn't exist or is empty, tell the user and ask where the spec lives or whether to create one — do not guess silently.

2. **Read the current spec file in full** before proposing any edit, so the diff is grounded in the actual current content (don't assume structure from memory of earlier turns).

3. **Draft the proposed change.**
   - Identify the precise section(s) of the spec affected.
   - Write the change as a minimal, targeted diff — don't rewrite unrelated parts of the document.
   - Preserve the existing structure, heading style, and tone of the document.

4. **Present the diff and stop.**
   - Show the proposed change as a clear before/after (a fenced diff-style block, using `-` for removed lines and `+` for added lines, is preferred for clarity).
   - Briefly state which file and section this affects.
   - Explicitly ask for confirmation, e.g. "Want me to apply this to `.claude/specs/<file>.md`?"
   - **Do not call any file-editing tool yet.** Wait for the user's next message.

5. **Apply only on explicit approval.**
   - If the user confirms (e.g. "yes", "apply it", "go ahead", "looks good"), use `str_replace` to make the exact edit shown in the diff — nothing more.
   - If the user requests adjustments instead of approving, revise the proposed diff and present it again (return to step 4). Do not write partial or guessed versions to disk.
   - If the user declines or says no, drop the change and do not touch the file.

6. **Confirm after writing.** After a successful edit, briefly confirm what was changed and where — no changelog entry, no extra narration.

## Notes

- Never batch up multiple unrelated proposed changes into one diff unless the user described them together.
- If the user's described change is ambiguous (e.g. unclear which section it belongs in), ask a short clarifying question before drafting the diff, rather than guessing.
- If the spec file doesn't yet contain a section relevant to the change, propose adding a new section in an appropriate place, and say so explicitly in the diff presentation.