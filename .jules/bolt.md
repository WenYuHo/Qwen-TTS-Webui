## 2026-02-22 - [Speaker Embedding and Prompt Caching]
**Learning:** Caching VoiceClonePromptItem (which contains extracted speaker embeddings and speech codes) significantly reduces the overhead of multi-segment synthesis. Extraction involves audio loading, resampling, and running two separate encoder models (speech tokenizer and speaker encoder), which can take >1s per segment. Caching these results reduces subsequent segment overhead to just the synthesis time.
**Action:** Always check for existing embeddings/prompts before triggering a full extraction pipeline in Qwen-TTS workflows.

## 2026-02-23 - [DOM Update and Voice Preview Caching]
**Learning:** Full re-renders of list components (like Story Blocks) during high-frequency polling (e.g., progress updates) cause significant UI lag and O(N) DOM thrashing. Implementing targeted updates via specific element IDs reduces this to O(1). Additionally, redundant ML synthesis for identical voice previews can be avoided with a simple client-side Map cache, saving seconds of backend processing time.
**Action:** Prioritize element-specific updates over full list re-renders for status/progress changes. Implement client-side caching for compute-heavy preview actions.

## 2026-02-24 - [Model Grouping in Podcast Engine]
**Learning:** In multi-speaker podcasts, alternating between profile types (e.g., Preset using CustomVoice model and Clone using Base model) causes the backend to repeatedly unload and reload 1.7B parameter models from disk/VRAM. This "thrashing" can add seconds of overhead to every segment. Grouping script items by their required model type and processing them in batches reduces model switches to the minimum count (O(M) instead of O(N)).
**Action:** When processing batch jobs that utilize different underlying ML models, always group items by model type before execution to minimize context-switching overhead.

## 2026-02-25 - [Dynamic Event Binding Consistency]
**Learning:** Mixing inline 'onclick' attributes with dynamic JS event attachment (via querySelector) leads to duplication and bugs if class names (like .js-play) are missing from the HTML strings. Using a consistent pattern of semantic 'js-' classes for all dynamic list items prevents runtime errors and simplifies DOM manipulation.
**Action:** Always verify that 'js-' classes used for event binding are present in the corresponding HTML templates.

## 2026-03-01 - [Vectorized Audio Assembly]
**Learning:** Using `pydub.AudioSegment` for multi-segment podcast assembly and BGM mixing/ducking is significantly slower (O(N) with high constant overhead for each overlay/slice) compared to vectorized NumPy operations. Pre-allocating a single project-wide array and using slice assignment for speech segments reduces assembly time by ~11x (from 2.3s to 0.2s for a 10-minute project). Sidechain ducking via NumPy array multiplication is also vastly more efficient than per-segment `AudioSegment` processing.
**Action:** Always prefer vectorized NumPy operations for audio mixing and concatenation over high-level library abstractions like pydub in performance-critical paths.

## 2026-03-01 - [In-Memory Caching for Audio and Embeddings]
**Learning:** In "Studio" workflows where users repeatedly regenerate podcasts with similar settings, redundant I/O (BGM loading) and redundant tensor math (mix embedding calculation) account for ~15-20% of non-inference latency. Implementing per-instance caches in the  for these artifacts provides significant speedups.
**Action:** Always check  and  before starting expensive audio processing or embedding mixing in synthesis pipelines. Use sorted JSON keys for mix configurations to ensure cache hits for identical settings.

## 2026-03-01 - [In-Memory Caching for Audio and Embeddings]
**Learning:** In "Studio" workflows where users repeatedly regenerate podcasts with similar settings, redundant I/O (BGM loading) and redundant tensor math (mix embedding calculation) account for ~15-20% of non-inference latency. Implementing per-instance caches in the `PodcastEngine` for these artifacts provides significant speedups.
**Action:** Always check `bgm_cache` and `mix_embedding_cache` before starting expensive audio processing or embedding mixing in synthesis pipelines. Use sorted JSON keys for mix configurations to ensure cache hits for identical settings.
