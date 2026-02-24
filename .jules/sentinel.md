## 2026-02-24 - [Partial Path Traversal via String Prefix Matching]
**Vulnerability:** The `PodcastEngine._resolve_paths` and `utils.validate_safe_path` functions used `str(path).startswith(str(base))` to validate that a resolved path was within an allowed directory.
**Learning:** This check can be bypassed if an attacker can access a directory that shares a common prefix with the allowed directory (e.g., if `/app/uploads` is allowed, `/app/uploads_secret` will also be accepted). String-based prefix matching is insufficient for path security.
**Prevention:** Always use `Path.is_relative_to(base)` or similar robust path comparison methods (like `os.path.commonpath`) to ensure a path is a literal child of the intended base directory.
