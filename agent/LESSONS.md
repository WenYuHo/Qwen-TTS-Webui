# Lessons Learned

Append one line per completed task. Prune oldest entries when > 30 lines.
Read this at session startup to avoid repeating past mistakes.

| Date | Lesson |
|:---|:---|
| 2026-03-13 | Duplicated rules across 5+ files burned tokens every session — consolidate to one source |
| 2026-03-13 | Reading all track files eagerly wastes ~50% of context budget — load on-demand only |
| 2026-03-13 | Two overlapping logs (EVOLUTION + IMPROVEMENT_LOG) caused confusion — use one canonical log |
