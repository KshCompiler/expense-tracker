---
name: spec
description: >
  Use this skill whenever the user runs `/spec` or asks to create a feature specification, spec document, or wants to plan a new website feature with a Git branch. Triggers on: "/spec", "create a spec", "write a feature spec", "spec out this feature", "create a specification for", "set up a feature branch and spec", "document this feature". Always use this skill when the user wants to define requirements, user stories, or acceptance criteria for a new feature and prepare the codebase for implementation.
---

# /spec — Feature Specification + Git Setup

A slash command that creates a complete, implementation-ready feature specification document and prepares the Git workflow (clean working tree → sync main → create feature branch).

---

## Step 1: Read Project Context

1. Read `CLAUDE.md` first. Follow **all** instructions, conventions, and constraints defined in it.
2. Scan additional files only as needed to understand: project structure, existing features, architecture, naming conventions, and dependencies.

---

## Step 2: Verify Git State

Run:
```bash
git status
```

- If the working tree is **clean**: proceed.
- If there are **uncommitted changes**:
  - Display the changes to the user.
  - Ask whether to **commit**, **stash**, or **discard** them.
  - **Do not switch branches** until the working tree is clean.

---

## Step 3: Sync Main Branch

```bash
git checkout main
git pull origin main
```

---

## Step 4: Gather Feature Information

Ask the user for the following (all in one message, not one at a time):

1. Feature number or ticket ID
2. Feature name
3. What functionality should be added
4. Problem being solved
5. Expected user behavior
6. UI/UX requirements
7. Technical constraints or dependencies
8. Acceptance criteria

Do not proceed to branch creation or spec writing until you have enough information. Ask follow-up questions if anything is ambiguous or missing.

---

## Step 5: Create Feature Branch

Generate a branch name from the feature name in **kebab-case**:

```bash
git checkout -b feature/<feature-name>
```

Example:
```bash
git checkout -b feature/user-profile-page
```

---

## Step 6: Create Specification Document

Write a complete spec using this structure:

```markdown
# Feature Specification

**Feature Number:** <id>
**Feature Name:** <name>

---

## Overview
Brief description of the feature.

## Problem Statement
What problem does this feature solve?

## Goals
- Goal 1
- Goal 2

## User Stories
- As a [user type], I want [action] so that [outcome].

## Functional Requirements
1. Requirement 1
2. Requirement 2

## Non-Functional Requirements
- Performance
- Security
- Accessibility
- Browser/device support

## UI/UX Requirements
Screens, components, interactions, validations.

## Technical Considerations
- Database changes
- API changes
- State management
- Dependencies
- Edge cases

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Out of Scope
Items explicitly not included in this implementation.

## Implementation Notes
Additional developer notes and considerations.
```

---

## Step 7: Save the Specification
check if specs folder exist or not inside .claude folder
if exist continue
if not make one then continue


save the file to
.claude/specs/<step_number>-<feature_slug>.md

## Constraints

- Always read `CLAUDE.md` before anything else.
- Never switch branches with a dirty working tree.
- Always sync `main` before branching.
- Branch names must be kebab-case.
- Never assume requirements — ask when information is missing.
- Produce a complete, implementation-ready document.
- Follow all project conventions from `CLAUDE.md`.