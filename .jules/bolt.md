## 2026-02-22 - [Speaker Embedding and Prompt Caching]
**Learning:** Caching VoiceClonePromptItem (which contains extracted speaker embeddings and speech codes) significantly reduces the overhead of multi-segment synthesis. Extraction involves audio loading, resampling, and running two separate encoder models (speech tokenizer and speaker encoder), which can take >1s per segment. Caching these results reduces subsequent segment overhead to just the synthesis time.
**Action:** Always check for existing embeddings/prompts before triggering a full extraction pipeline in Qwen-TTS workflows.
