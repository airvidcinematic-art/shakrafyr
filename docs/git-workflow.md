# Git workflow — Convert432

Local simplified GitFlow. No GitHub remote until you ask to push.

| Branch / tree | Role |
|---------------|------|
| `main` | Stable snapshot (primary checkout when the worktree layout is on) |
| `dev` | Daily SSOT — product work lands here |
| `.worktrees/dev` | Checkout of `dev` when primary is frozen on `main` |
| `feature/<name>` | Cut off `dev`; merge back; delete the worktree |

```
main (stable) → dev (daily) → feature/* → merge to dev → delete feature worktree
promote: merge dev → main
```

- Conventional commits (`feat:`, `fix:`, `docs:`, `chore:`).
- Never `git push` unless asked. Private GitHub, no PRs — direct merge feature → dev → main.
- `.worktrees/` is gitignored; registered with `git worktree`, never `rm -rf`.
- ConvertedLibrary / play-cache stay local.
