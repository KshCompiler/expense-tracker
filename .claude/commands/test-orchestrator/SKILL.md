---
name: test-orchestrator
description: >
  Custom /test command that orchestrates two subagents sequentially: first test-case-writer
  (generates test cases from code or description), then test-runner (executes and reports results).
  Trigger this skill whenever the user types /test, /runtests, or asks to "write and run tests",
  "generate and execute test cases", or "test this code". Always use this skill for any multi-step
  test generation + execution workflow, even if the user just says "test this" or pastes code and
  says "check it".
---

# Test Orchestrator

Orchestrates two subagents in sequence to write and run test cases for user-provided code.

## Trigger

This skill activates on:
- `/test` or `/runtests` command
- Natural language like "write and run tests", "test this code", "generate test cases and run them"

---

## Workflow

### Step 1 — Read the subagent instructions

Before spawning anything, read both agent files so you understand what each one expects as input and what it produces as output.

- **Test Case Writer agent**: `.claude/agents/test-case-writer.md`
- **Test Runner agent**: `.claude/agents/test-runner.md`



---

### Step 2 — Collect input from the user

If the user hasn't already provided code or a description, ask:

> "Please paste the code or describe what you want tested."

Accepted inputs:
- Raw code (any language)
- Uploaded file
- Natural language description of a function or module

---

### Step 3 — Spawn test-case-writer subagent

Using the instructions from `test-case-writer.md`, run the subagent with the user's code/description as input.

**What to pass in:**
- The full code or description
- Any constraints the user mentioned (language, framework, edge cases to focus on)

**What to collect:**
- The generated test cases (as code, a list, or whatever format the agent produces)

---

### Step 4 — Spawn test-runner subagent

Using the instructions from `test-runner.md`, pass the output from Step 3 directly as input.

**What to pass in:**
- The test cases generated in Step 3
- The original code (so the runner has something to test against)

**What to collect:**
- Pass/fail results
- Any errors or stack traces
- Summary statistics (X passed, Y failed)

---

### Step 5 — Report results to the user

Present a clean summary:

```
✅ Tests Written: <N>
✅ Passed: <N>
❌ Failed: <N>

[List of failing tests with brief reason, if any]
```

If all tests pass, say so clearly. If some fail, offer to investigate or fix the code.

---

## Notes

- Always run writer → runner in that order. Never run them in parallel.
- If the writer subagent fails or produces no output, stop and report the error before attempting the runner.
- If the user only wants test cases written (not run), they can say `/test --write-only` — in that case skip Step 4.
- If the user only wants to run existing tests, they can say `/test --run-only` — in that case skip Step 3 and ask them to paste the test cases.