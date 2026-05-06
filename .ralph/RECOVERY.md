# Recovery

Before picking new work, assess state:

| Worktree | Verification | Meaning | Action |
| --- | --- | --- | --- |
| clean | pass | likely complete or no work started | confirm behavior and close only if acceptance passes |
| clean | fail | baseline broken | fix/block before new work |
| dirty | pass | partial work may be good | inspect diff, finish, verify |
| dirty | fail | partial work is broken | read handoff, fix or block |

If intent is unclear, record what you found and block the task. Do not silently close it.
