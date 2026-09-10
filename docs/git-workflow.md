# Git workflow — Convert432

Local simplified GitFlow. **No GitHub remote until you ask to push.**

## Layout as of 2026-09-10

| Tree | Branch | Role |
|------|--------|------|
| `C:\Users\shaon\Projects\Convert432` | `dev` | Daily SSOT — this is where you edit and `npm run tauri dev` |
| `.worktrees\main` | `main` | Frozen shell snapshot (`207b058`) |

This is **inverted vs GateMaster Lite** (GML: primary = `main`, daily = `.worktrees\dev`). Git will not check out `dev` in two places. To flip later: stop the app, `git checkout main` in the primary tree, `git worktree add .worktrees/dev dev`.

```
main (stable) → dev (daily) → feature/* → merge to dev → delete feature worktree
promote: merge dev → main
```

- Conventional commits (`feat:`, `fix:`, `docs:`, `chore:`, `plan:`).
- Never `git push` unless asked. Private GitHub, no PRs — direct merge feature → dev → main.
- `.worktrees/` is gitignored; registered with `git worktree`, never `rm -rf`.
- `ConvertedLibrary/` and play-cache stay local.
