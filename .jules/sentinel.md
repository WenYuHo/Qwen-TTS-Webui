## 2026-02-24 - [Partial Path Traversal via String Prefix Matching]
**Vulnerability:** The `PodcastEngine._resolve_paths` and `utils.validate_safe_path` functions used `str(path).startswith(str(base))` to validate that a resolved path was within an allowed directory.
**Learning:** This check can be bypassed if an attacker can access a directory that shares a common prefix with the allowed directory (e.g., if `/app/uploads` is allowed, `/app/uploads_secret` will also be accepted). String-based prefix matching is insufficient for path security.
**Prevention:** Always use `Path.is_relative_to(base)` or similar robust path comparison methods (like `os.path.commonpath`) to ensure a path is a literal child of the intended base directory.

## 2026-02-25 - [Role-based Path Traversal in Temp Files]
**Vulnerability:** User-provided `role` names were used to construct temporary filenames for voice previews without sufficient sanitization, potentially allowing path traversal if the filename was not strictly controlled.
**Learning:** Even if a filename is constructed from multiple parts, if one part is user-controlled and can contain traversal characters (like `../`), it can escape the intended directory.
**Prevention:** Use randomly generated names (like UUIDs) for temporary files and avoid using user-controlled strings in filesystem paths whenever possible.

## 2026-02-26 - [Disk Exhaustion via Transient Resource Creation]
**Vulnerability:** The `/api/voice/preview` endpoint wrote temporary WAV files to a public static directory (`src/static/previews`) using UUIDs but lacked a cleanup mechanism. This could lead to disk space exhaustion (DoS) if called repeatedly.
**Learning:** Writing transient files to disk for short-lived UI requests is a resource management risk. Even with unique names, persistent storage of temporary data is a liability.
**Prevention:** Prefer memory-buffered responses (e.g., `StreamingResponse` with `io.BytesIO`) for short-lived assets. Always use generic error messages in public APIs to prevent leaking internal stack traces or environment details.

## 2026-03-01 - [Path Traversal in Asset Upload]
**Vulnerability:** The `/api/assets/upload` endpoint trusted the user-provided `file.filename` without sanitization, allowing attackers to write files outside the intended `shared_assets/` directory using `../` sequences.
**Learning:** FastAPI `UploadFile.filename` is not inherently safe and must be sanitized before being used in filesystem operations.
**Prevention:** Always use `Path(filename).name` to extract only the base name of a file, and validate the resulting path using `Path.is_relative_to(base)` before performing any write operations.
