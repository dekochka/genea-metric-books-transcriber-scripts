# Codebase Concerns

**Analysis Date:** 2026-02-21

## Tech Debt

**Monolithic transcribe.py File:**
- Issue: Main script has grown to 5,587 lines with all core logic in a single file
- Files: `transcribe.py`
- Impact: Difficult to navigate, test, and maintain. High cognitive load for modifications. Hard to isolate concerns.
- Fix approach: Refactor into modular architecture with separate files for strategies (auth, image source, output, AI client), utilities (image number extraction, cost calculation), and core orchestration

**Bare Exception Handlers:**
- Issue: One bare `except:` clause without specific exception type
- Files: `wizard/preflight_validator.py:338`
- Impact: Catches all exceptions including system exits and keyboard interrupts. Hides bugs and makes debugging difficult.
- Fix approach: Replace with specific exception types (`except (ValueError, OSError):`) or at minimum `except Exception:`

**Multiple Return None Without Clear Error Signaling:**
- Issue: 50+ functions return `None` on error/failure without raising exceptions or clear error states
- Files:
  - `transcribe.py:2164`, `2170`, `2245`, `2342`, `3010`, `3013`, `3047`, `3067`, `3089`, `3255`
  - `wizard/wizard_controller.py:111`, `114`, `140`, `172`, `182`, `192`, `197`
  - `wizard/title_page_extractor.py:79`, `87`, `91`, `103`, `117`, `124`, `146`, `169`, `296`, `307`, `385`, `388`
  - `wizard/steps/context_collection_step.py:490`, `501`, `517`, `525`, `560`, `585`, `614`, `650`, `669`, `687`
  - `wizard/steps/processing_settings_step.py:275`, `286`, `301`, `350`, `364`
  - `recovery_script.py:232`, `235`, `295`
- Impact: Callers must check for `None` which is easy to forget. Silent failures cascade through system. Makes control flow unclear.
- Fix approach: Use exceptions for errors, use Optional[T] type hints with explicit error handling strategy, or return Result/Either types

**Strategy Pattern with Pass-Through Exception Handling:**
- Issue: Abstract base classes define methods with `pass` but callers wrap all implementations in generic try-except
- Files: `transcribe.py:465`, `475`, `537`, `550`, `563`, `962`, `1272`, `1284`, `1298`
- Impact: Swallows implementation-specific error information. Makes debugging strategy failures difficult.
- Fix approach: Define specific exception types for each strategy failure mode and handle them appropriately at call site

**Recovery Script Coupling:**
- Issue: Recovery script hardcodes assumptions about log format and duplicates authentication/API logic
- Files: `recovery_script.py`
- Impact: Brittle to log format changes. Maintenance burden of two authentication paths. No tests for recovery path.
- Fix approach: Extract log parsing into shared library. Use same auth strategy classes as main script. Add integration tests.

## Known Bugs

**Platform-Specific Signal Handling:**
- Symptoms: Uses Unix-only `signal.SIGALRM` for API call timeouts
- Files: `transcribe.py:2738`, `2812-2813`, `2828`, `2891`, `2946`, `2966`
- Trigger: Running on Windows where `signal.SIGALRM` doesn't exist
- Workaround: Code will crash on Windows. No current workaround in codebase.
- Fix: Use `threading.Timer` or `concurrent.futures.Future.result(timeout=)` for cross-platform timeout support

**Progress Bar Count Issues (Partially Fixed):**
- Symptoms: Progress bar showing incorrect counts during document writing
- Files: `transcribe.py` (output strategy finalization)
- Trigger: Batch writing operations that update progress bars
- Workaround: Recent fix in v0.5-beta-wizard-mode but may have edge cases
- Fix: Comprehensive audit of all progress bar update call sites

**Image Number Buffer Insufficient for Sparse Naming:** ✅ FIXED
- Status: Fixed in Phase 2 (2026-02-21)
- Previous symptoms: Script would not fetch enough images if filenames were very sparse (e.g., gaps of 100+ between numbers)
- Previous trigger: Using `image_start_number=500` with sparse numbering (500, 520, 700, 800), 200-image buffer would miss higher-numbered files
- Fix implemented: Fetch ALL images first with pagination (up to user's `max_images` or 10,000 safety limit), then filter by image number range
- Files changed: `transcribe.py:2437-2474`
- Backward compatibility: Preserved - respects user's `max_images` config if provided
- Test coverage: 5 comprehensive unit tests added covering sparse, contiguous, empty, single-image, and pagination scenarios

## Security Considerations

**Credential Files Present in Repository:**
- Risk: Two client secret files exist in repository root (excluded from .gitignore but still physically present)
- Files: `client_secret.json`, `client_secret_ok.json`
- Current mitigation: Files listed in `.gitignore` (line 13)
- Recommendations:
  - Verify files are not in git history with `git log --all --full-history -- client_secret*.json`
  - If committed previously, use `git filter-repo` to remove from history
  - Move to `~/.config/genea-transcriber/` or environment-specific location outside repository
  - Document required credential location in README

**API Key Handling via Environment Variable:**
- Risk: API keys passed through `GEMINI_API_KEY` environment variable may leak in process listings or logs
- Files: `transcribe.py:488-490`, `wizard/preflight_validator.py:128`
- Current mitigation: Code doesn't log the actual key value
- Recommendations:
  - Document secure key storage (e.g., using system keyring)
  - Add warning in docs about not committing `.env` files
  - Consider integrating with system keychains (macOS Keychain, Windows Credential Manager)

**Verbose Error Messages May Leak Credentials:**
- Risk: Exception messages and tracebacks might contain API keys or tokens
- Files: `transcribe.py:2902-2904` (full traceback logging)
- Current mitigation: None detected
- Recommendations:
  - Sanitize exception messages before logging
  - Add filter to redact patterns like `AIza.*`, `sk-.*`, `Bearer .*` from logs
  - Review all `logging.debug` calls that log full objects

**Application Default Credentials in Repository Root:**
- Risk: File `application_default_credentials.json` contains refresh tokens
- Files: `application_default_credentials.json`, `application_default_credentials.json.backup`
- Current mitigation: Excluded in `.gitignore` (line 11-12)
- Recommendations: Same as client_secret.json - verify not in git history, move outside repo

## Performance Bottlenecks

**Sequential Image Processing:**
- Problem: Images processed one at a time with no parallelization
- Files: `transcribe.py` main processing loop (lines 4000-4500 estimated)
- Cause: Single-threaded loop with API calls taking 30-120 seconds each
- Improvement path:
  - Implement concurrent processing with `concurrent.futures.ThreadPoolExecutor`
  - Respect API rate limits (60 requests/minute for Gemini)
  - Start with 3-5 concurrent workers to balance throughput and rate limits
  - Estimated speedup: 3-5x for I/O-bound API calls

**Large File Reading and Parsing:**
- Problem: Image files read entirely into memory as bytes
- Files: `transcribe.py` (image download and processing)
- Cause: `get_image_bytes()` loads full image into memory for each processing attempt
- Improvement path:
  - Cache downloaded images to disk temporarily
  - Reuse cached bytes on retry instead of re-downloading
  - Implement streaming/chunked processing for very large images

**Google Docs API Rate Limiting in Recovery Script:**
- Problem: Manual rate limiting with sleep() calls instead of exponential backoff
- Files: `recovery_script.py:348-373`
- Cause: Google Docs has 60 requests/minute quota, script uses fixed 55 req/min with buffer
- Improvement path:
  - Use exponential backoff with jitter
  - Implement proper rate limiter with token bucket algorithm
  - Batch multiple text insertions into single `batchUpdate` call (currently one per page)

**Cost Calculation Inefficiency:**
- Problem: Iterates through all pages twice (once for metrics, once for cost)
- Files: `transcribe.py:3370-3440` (calculate_cost function)
- Cause: Metrics collection and cost calculation happen separately
- Improvement path: Calculate cost during metrics collection in single pass

## Fragile Areas

**Image Number Extraction with Multiple Patterns:**
- Files: `transcribe.py:2150-2320`, `2515-2600`
- Why fragile: Complex regex patterns with multiple fallback strategies. Silent failures return `None`.
- Safe modification: Add comprehensive test suite with real filename samples from each archive. Log which pattern matched for each file.
- Test coverage: Has dedicated test file `tests/unit/test_image_number_extraction.py` but needs expansion

**Wizard Context Extraction with AI:**
- Files: `wizard/title_page_extractor.py`
- Why fragile: Depends on AI model responses being parseable JSON. No schema validation. 388 lines of parsing logic with multiple `return None` paths.
- Safe modification:
  - Add JSON schema validation with `jsonschema` library
  - Implement retry with refined prompts if parsing fails
  - Add fallback to manual entry if AI extraction fails completely
- Test coverage: Has unit tests in `tests/unit/test_title_page_extractor.py`

**Config Migration and Normalization:**
- Files: `transcribe.py:56-200` (load_config, detect_mode, normalize_config functions)
- Why fragile: Handles both legacy flat YAML and new nested structure. Complex detection logic with fallbacks. Easy to break backward compatibility.
- Safe modification:
  - Always test with both legacy and new config formats
  - Use compatibility test suite in `tests/compatibility/test_legacy_configs.py`
  - Document config format changes in CHANGELOG
- Test coverage: Good - dedicated compatibility tests exist

**Prompt Assembly with Template Variables:**
- Files: `wizard/prompt_assembler.py:259`
- Why fragile: String template substitution with `{{VARIABLE}}` syntax. Silent failures if variables missing (line 114: bare `pass`).
- Safe modification:
  - Add validation that all template variables are provided
  - Raise clear exception if variable missing rather than silently skipping
  - Add template validation in preflight checks
- Test coverage: Has tests in `tests/unit/test_prompt_assembler.py`

**Logging Setup with Handler Cleanup:**
- Files: `transcribe.py:420-426`
- Why fragile: Manually removes all logging handlers on each setup. Can interfere with pytest, IDE debuggers, or other logging configurations.
- Safe modification:
  - Use named loggers (`logging.getLogger(__name__)`) instead of root logger
  - Only clear handlers specific to this application
  - Consider using `logging.config.dictConfig()` for more robust setup
- Test coverage: Integration tests may miss this if they don't check log output

## Scaling Limits

**Google Drive Folder Image Fetching:**
- Current capacity: Fetches up to 1000 images with pagination
- Limit: No hard limit but performance degrades significantly >500 images
- Scaling path:
  - Implement cursor-based pagination for truly large folders (>10k images)
  - Add folder organization strategy (subfolders by year/batch)
  - Consider cloud-native batch processing (Cloud Run jobs, batch API)

**In-Memory Page Storage:**
- Current capacity: Stores all transcribed pages in memory before writing
- Limit: ~1000 pages (estimated 5MB of text) before memory pressure
- Scaling path:
  - Stream pages to disk incrementally instead of accumulating in memory
  - Use temporary SQLite database for page storage during processing
  - Already partially implemented in MarkdownOutput with temp file

**Cost Estimation Precision:**
- Current capacity: Accurate for single runs, no cumulative tracking
- Limit: No way to track costs across multiple runs or sessions
- Scaling path:
  - Implement cost tracking database (SQLite)
  - Add monthly/project-level cost aggregation
  - Create cost reporting dashboard

## Dependencies at Risk

**python-docx (Optional Dependency):**
- Risk: Word output functionality fails if not installed (lines 42-52)
- Impact: Users lose Word document output capability but script continues
- Migration plan: Make it truly optional by removing import error warnings or make it required in `requirements.txt`

**google-genai Library Warnings:**
- Risk: Library generates informational warnings that clutter output
- Impact: User experience degradation, warnings suppressed in title extraction (wizard/title_page_extractor.py)
- Migration plan: Monitor library updates, file issues upstream, implement warning filters application-wide

**OAuth2 Flow Complexity:**
- Risk: Google OAuth2 libraries have complex dependency chains (`google-auth-oauthlib`, `google-auth-httplib2`)
- Impact: Breaking changes in auth flow could break googlecloud mode entirely
- Migration plan:
  - Pin major versions in requirements.txt (currently unpinned)
  - Add integration tests that verify actual OAuth flow
  - Document manual credential refresh process

## Missing Critical Features

**No Resume/Checkpoint Capability:**
- Problem: If script crashes after processing 50 images, must restart from beginning
- Blocks: Processing large archives (500+ images) reliably
- Recommendation: Implement checkpoint file that tracks completed images. Check on startup and skip already-processed images.

**No Batch Job Management:**
- Problem: Cannot queue multiple processing jobs or run them overnight unattended
- Blocks: Professional genealogy researcher workflows with dozens of archives
- Recommendation: Add job queue system (Redis + worker) or simple file-based queue

**Limited Output Format Options:**
- Problem: Only Markdown (local) and Google Docs (googlecloud) supported. No PDF, DOCX file, or HTML.
- Blocks: Users who need portable document formats or archival-quality output
- Recommendation: Add PDF export using reportlab, DOCX file generation using python-docx finalization

**No Audit Trail of AI Responses:**
- Problem: AI response logs are separate files, not linked to output documents
- Blocks: Verifying transcription accuracy, debugging errors, quality control
- Recommendation: Embed metadata in output (AI model version, confidence scores, timestamp)

## Test Coverage Gaps

**Integration Test for Full Googlecloud Mode:**
- What's not tested: End-to-end flow from Google Drive authentication to Google Docs creation
- Files: `tests/integration/test_googlecloud_mode.py` exists but likely uses mocks
- Risk: Authentication flow, Drive API, Docs API interactions could break silently
- Priority: High - core functionality

**Error Recovery Paths:**
- What's not tested: Behavior when API calls timeout after all retries exhausted
- Files: Timeout error handling in `transcribe.py:2889-2966`
- Risk: Unknown behavior when all 3 retry attempts (1min, 2min, 5min) fail
- Priority: Medium - happens rarely but catastrophic when it does

**Signal Timeout Mechanism:**
- What's not tested: Cross-platform signal handling (known to fail on Windows)
- Files: `transcribe.py:2812-2828`
- Risk: Script crashes on Windows with no fallback
- Priority: High - affects entire Windows user base

**Wizard Mode Edge Cases:**
- What's not tested: User cancellation mid-wizard, invalid inputs, concurrent wizard runs
- Files: `wizard/wizard_controller.py`, wizard step classes
- Risk: Partial config files left behind, unclear error messages
- Priority: Medium - affects user experience but not data integrity

**Cost Calculation Accuracy:**
- What's not tested: Edge cases like zero tokens, missing usage metadata, cached tokens
- Files: `transcribe.py:3370-3440`
- Risk: Incorrect cost estimates mislead users about API spending
- Priority: Low - financial impact is small but user trust is affected

**Config Migration and Backward Compatibility:**
- What's not tested: Migration from very old config formats (pre-v0.4)
- Files: `transcribe.py:56-200`, `tests/compatibility/test_legacy_configs.py`
- Risk: Users upgrading from old versions may experience config errors
- Priority: Low - can document manual migration steps

---

*Concerns audit: 2026-02-21*
