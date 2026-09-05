# Git hooks

Enable these hooks for this worktree only:

```sh
git config --worktree core.hooksPath .githooks
```

This replaces obsolete Husky hooks without modifying the shared hooks used by
legacy branches. The pre-commit hook checks staged source whitespace; generated
frontend bundles are excluded. Go tests and frontend checks remain CI gates.
