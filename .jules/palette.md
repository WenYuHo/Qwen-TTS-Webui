# Palette's Journal - UX & Accessibility Learnings

This journal tracks critical UX and accessibility learnings discovered during the development of Qwen-TTS Podcast Studio.

## 2025-05-15 - Unifying Audio Preview Patterns
**Learning:** In a multi-manager SPA, centralizing audio playback to a global persistent player (like `#preview-player`) improves user focus and prevents "audio clutter" from multiple detached Audio objects.
**Action:** Always route source URLs to the global player and implement consistent loading feedback (spinners) on the triggering elements.
