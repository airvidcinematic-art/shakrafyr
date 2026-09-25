# Git workflow — Convert432 / ShakraFyr

Local simplified GitFlow with a **public GitHub remote** (`origin` = `https://github.com/airvidcinematic-art/shakrafyr.git`). Nothing is pushed unless asked.

## Layout (as of 2026-09-25)

| Tree | Branch | Role |
|------|--------|------|
| `C:\Users\shaon\Projects\Convert432` | `dev` | Daily SSOT — this is where you edit and `npm run tauri dev` |
| `.worktrees\main` | `main` | Frozen stable snapshot (`e083c5e`) |

This is **inverted vs GateMaster Lite** (GML: primary = `main`, daily = `.worktrees\dev`). Git will not check out `dev` in two places. To flip later: stop the app, `git checkout main` in the primary tree, `git worktree add .worktrees/dev dev`.

```
main (stable) ← promoted from dev
dev (daily) ← feature/* → merge to dev → delete feature worktree
promote: merge dev → main (fast-forward only; a fresh clone defaults to `main`)
```

## Rules

- Conventional commits (`feat:`, `fix:`, `docs:`, `chore:`, `plan:`).
- **Never** `git push` unless explicitly asked. When the user says "online" / "share":
  1. `git push origin dev`
  2. Fast-forward `main`: `git push origin main` (or `git push origin dev:main` when in sync)
  - `origin/dev` and `origin/main` should stay at the same commit for a clean clone.
- No PRs, no reviewers — solo dev. Direct merge: feature → `dev` → `main`.
- `.worktrees/` is gitignored; registered with `git worktree`, never `rm -rf`.
- `ConvertedLibrary/` and play-cache stay local (never committed).