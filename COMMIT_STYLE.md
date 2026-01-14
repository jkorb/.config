# Commit Message Style Guide

## Goals
- Make history easy to scan and grep.
- Capture why when it matters, not just what.
- Keep messages consistent across tools and editors.

## Format
- Use: `<scope>: <imperative summary>`
- Summary: present tense, no period, <= 60 characters.
- Scope: top-level area or domain (e.g. `codex`, `tmux`, `nvim`, `repo`).
- Body: optional; wrap at 72 chars; explain rationale, risks, or follow-ups.

## Examples
- `codex: add content image to notifications`
- `tmux: simplify session attach script`
- `repo: ignore local Codex state files`

## When to include a body
- Non-obvious changes
- Behavior changes or potential regressions
- Anything that will matter in 30 days
