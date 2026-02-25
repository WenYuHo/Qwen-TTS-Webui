## 2026-02-24 - [Partial Path Traversal via String Prefix Matching]
**Vulnerability:** The `PodcastEngine._resolve_paths` and `utils.validate_safe_path` functions used `str(path).startswith(str(base))` to validate that a resolved path was within an allowed directory.
**Learning:** This check can be bypassed if an attacker can access a directory that shares a common prefix with the allowed directory (e.g., if `/app/uploads` is allowed, `/app/uploads_secret` will also be accepted). String-based prefix matching is insufficient for path security.
**Prevention:** Always use `Path.is_relative_to(base)` or similar robust path comparison methods (like `os.path.commonpath`) to ensure a path is a literal child of the intended base directory.

## 2026-02-25 - [Role-based Path Traversal in Temp Files]
**Vulnerability:** User-provided `role` names were used to construct temporary filenames for voice previews without sufficient sanitization, potentially allowing path traversal if the filename was not strictly controlled.
**Learning:** Even if a filename is constructed from multiple parts, if one part is user-controlled and can contain traversal characters (like `../`), it can escape the intended directory.
**Prevention:** Use randomly generated names (like UUIDs) for temporary files and avoid using user-controlled strings in filesystem paths whenever possible.
