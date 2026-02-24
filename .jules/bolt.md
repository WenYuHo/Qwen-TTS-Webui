## 2026-02-22 - [Speaker Embedding and Prompt Caching]
**Learning:** Caching VoiceClonePromptItem (which contains extracted speaker embeddings and speech codes) significantly reduces the overhead of multi-segment synthesis. Extraction involves audio loading, resampling, and running two separate encoder models (speech tokenizer and speaker encoder), which can take >1s per segment. Caching these results reduces subsequent segment overhead to just the synthesis time.
**Action:** Always check for existing embeddings/prompts before triggering a full extraction pipeline in Qwen-TTS workflows.

## 2026-02-23 - [DOM Update and Voice Preview Caching]
**Learning:** Full re-renders of list components (like Story Blocks) during high-frequency polling (e.g., progress updates) cause significant UI lag and O(N) DOM thrashing. Implementing targeted updates via specific element IDs reduces this to O(1). Additionally, redundant ML synthesis for identical voice previews can be avoided with a simple client-side Map cache, saving seconds of backend processing time.
**Action:** Prioritize element-specific updates over full list re-renders for status/progress changes. Implement client-side caching for compute-heavy preview actions.
