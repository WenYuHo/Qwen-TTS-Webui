# Agent Lessons Learned

This file tracks important architectural decisions, bug patterns, and workflow improvements to prevent repeating mistakes.

| Date | Lesson |
|:---|:---|
| 2026-03-13 | Restore `symphony_start.py` to root to ensure multi-agent launcher is visible. |
| 2026-03-13 | Use simple quoting and no newlines in Windows `cmd /k` mission strings to prevent CLI help menu triggers. |
