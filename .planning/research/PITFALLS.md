# Pitfalls Research - Python Bug Fixes

**Domain:** Python bug fixing (cross-platform, UI/progress bars, edge cases)
**Researched:** 2026-02-21
**Confidence:** HIGH

## Critical Pitfalls

### Pitfall 1: Cross-Platform Incompatibilities Missed in Development Environment

**What goes wrong:**
Bug fixes are tested and validated in developer's environment (typically Unix/macOS) but fail catastrophically on Windows due to platform-specific APIs that don't exist or behave differently. The signal handling bug (using `signal.SIGALRM` which doesn't exist on Windows) is a textbook example.

**Why it happens:**
- Developers work on single platform (macOS/Linux) and don't test on Windows
- Platform differences are non-obvious (e.g., signal module has different capabilities)
- CI/CD may only test on Linux containers
- Assumptions about OS-level features being universal

**How to avoid:**
- **Always check platform compatibility** for any OS-level API usage (signal, process, threading, file paths)
- Use cross-platform abstractions: `threading.Timer` instead of `signal.SIGALRM`, `pathlib.Path` instead of string paths
- Test on all target platforms before declaring fix complete
- Add platform matrix to CI/CD (GitHub Actions: ubuntu-latest, macos-latest, windows-latest)
- Use `sys.platform` checks to provide platform-specific implementations with graceful fallbacks

**Warning signs:**
- Import statements using OS-specific modules: `signal`, `fcntl`, `pwd`, `grp`
- Code that only works on Unix: `os.fork()`, `os.mkfifo()`, Unix-only signals
- Path manipulation using string concatenation with `/` or `\`
- Timeout mechanism implementation changes (new signal usage)

**Phase to address:**
Phase 1 (Signal handling fix) - Must verify cross-platform compatibility before implementation. Phase 4 (Integration tests) - Must include platform-specific testing.

---

### Pitfall 2: Breaking Existing Functionality Through Incomplete Context

**What goes wrong:**
Bug fix addresses the reported symptom but doesn't understand the full context of why code was written a certain way. This causes regressions where previously working scenarios break. Example: Fixing progress bar counts in batch writing might break finalization counts if writer doesn't understand the full progress bar lifecycle.

**Why it happens:**
- Focus on narrow bug reproduction instead of understanding full feature
- Monolithic codebase makes tracing call paths difficult (5,587-line transcribe.py)
- Multiple related code paths (LOCAL vs GOOGLECLOUD modes) using same components
- Progress bar updates scattered across processing loop, batch writing, and finalization
- No comprehensive documentation of component interactions

**How to avoid:**
- **Trace all code paths** that touch the buggy component before making changes
- Use grep to find all call sites: `grep -n "progress.update" transcribe.py`
- Document current behavior: "Progress bar advances after transcription (line 4655), during batch write (line 5055), and finalization"
- Test both modes (LOCAL and GOOGLECLOUD) since they share strategy implementations
- Create regression test suite covering all affected code paths
- Run full test suite before declaring fix complete

**Warning signs:**
- Bug fix touches shared utility functions or strategy implementations
- Code has multiple similar-looking patterns (copy-paste variations)
- Fix only tested in one mode but code is used in both
- Test coverage shows only 50-70% of related code paths exercised
- "This fix works in my test case" without verifying edge cases

**Phase to address:**
Phase 2 (Progress bar fixes) - Must audit ALL progress bar update sites. Phase 3 (Image buffer fix) - Must verify interaction with retry mode and image filtering logic.

---

### Pitfall 3: Insufficient Error Path Testing After Timeout Fixes

**What goes wrong:**
After implementing cross-platform timeout mechanism (switching from `signal.SIGALRM` to `threading.Timer` or `concurrent.futures`), the error paths aren't properly tested. The new timeout mechanism might not properly cancel, might leave threads running, or might swallow exceptions that signal-based approach would propagate.

**Why it happens:**
- Focus on happy path: "Does timeout work?" instead of "What happens when timeout fires?"
- Threading introduces complexity: resource cleanup, exception propagation, thread lifecycle
- `concurrent.futures.TimeoutError` vs `signal.alarm` exception handling are different
- Retry logic assumes timeout exceptions behave like previous implementation
- Error path testing is hard (requires simulating slow API calls)

**How to avoid:**
- **Test all timeout scenarios explicitly:**
  1. Normal completion before timeout (happy path)
  2. Timeout on first attempt, success on retry
  3. Timeout exhausting all retries (critical failure path)
  4. Multiple concurrent operations timing out
- Verify exception types match expectations in retry logic
- Check thread/executor cleanup: no zombie threads after timeouts
- Verify cancellation: timed-out operations don't complete after timeout
- Test resource cleanup: file handles, network connections, API clients
- Add integration test simulating slow API with mock delays

**Warning signs:**
- Timeout mechanism change without explicit error path tests
- Generic `except Exception` catching new timeout errors
- No verification that retry logic handles new exception types
- Thread pool or executor created but never explicitly shut down
- Timeout fires but API call continues running in background

**Phase to address:**
Phase 1 (Signal handling fix) - Must include comprehensive timeout error testing. Phase 4 (Integration tests) - Must verify timeout behavior when all retries exhausted.

---

### Pitfall 4: Edge Case Fixes That Create New Edge Cases

**What goes wrong:**
Fixing the image buffer issue (sparse filename numbering) by "fetching all images first" introduces new problems: performance degradation with thousands of images, memory usage with large image lists, timeout on folder enumeration in Drive API.

**Why it happens:**
- Simple fix ("fetch everything!") without considering scale limits
- Original buffer approach had reason: performance/memory tradeoff
- New approach trades one edge case problem for different edge case problems
- Didn't test with realistic large datasets

**How to avoid:**
- **Understand why original approach existed** before replacing it
- Test fix at scale: 10 images, 100 images, 1000 images, 5000 images
- Consider hybrid approach: fetch larger buffer (500-1000) instead of "all"
- Implement pagination for truly large folders (Google Drive has 1000-item page size)
- Add early warnings: "Folder has 5000 images, this may be slow"
- Profile performance: time the list_images() call with various folder sizes
- Consider lazy loading: fetch on-demand as processing progresses

**Warning signs:**
- Fix replaces one heuristic (buffer size) with another extreme (fetch all)
- No testing with large datasets
- API calls without pagination
- Loading full result sets into memory
- No consideration of timeout at the API call level
- "This fixes my test case with 20 images"

**Phase to address:**
Phase 3 (Image buffer fix) - Must test with varied folder sizes and implement pagination. Must profile performance impact.

---

### Pitfall 5: Test-Induced Damage - Tests That Don't Match Production

**What goes wrong:**
Tests for bug fixes use mocks, stubs, or simplified scenarios that don't match production behavior. Test passes, bug fix ships, but real-world usage still fails. Example: Testing timeout mechanism with mock API client that completes instantly, missing the actual timeout behavior.

**Why it happens:**
- Over-reliance on unit tests with heavy mocking
- Integration tests use test doubles instead of real dependencies
- Test data doesn't match production complexity
- Time-dependent behavior hard to test (timeouts, retries, exponential backoff)
- Platform-specific behavior not testable in CI environment

**How to avoid:**
- **Mix test types appropriately:**
  - Unit tests: Logic, validation, error handling
  - Integration tests: Real API calls (with VCR recording), actual file I/O
  - Manual tests: Cross-platform verification, long-running operations
- Use real dependencies in integration tests when possible
- For timeout tests: use actual delays, not mocks that complete instantly
- Test with production-like data: actual Google Drive folders, real image files
- Document what can't be automated: "Manual Windows verification required"
- Use time mocking carefully: `freezegun` for date logic, real `time.sleep()` for timing

**Warning signs:**
- All tests complete in <1 second (no real I/O or delays)
- 100% mocked dependencies in "integration" tests
- Tests don't actually exercise the bug that was fixed
- "Test passes but bug still reproduces manually"
- No tests for platform-specific code paths
- Using `@patch` on the exact function being fixed

**Phase to address:**
Phase 4 (Test coverage) - Must distinguish unit vs integration tests. Must include real timeout delays. Manual Windows verification documented.

---

### Pitfall 6: Progress Bar Lifecycle Confusion

**What goes wrong:**
Progress bars in batch processing have complex lifecycle: initialize with total count, update during processing, update during writing, finalize with summary. Bug fixes that adjust counts at one stage break counts at another stage. Recent v0.5-beta fix may have edge cases in document finalization.

**Why it happens:**
- Progress bar updates scattered across codebase (lines 4569, 4655, 4722, 4790, 4924, 4989, 5032, 5055, 5068)
- Different semantics: `advance=0` (update description), `advance=1` (increment count)
- Batch writing adds progress updates outside main processing loop
- Error paths need progress updates to avoid stuck bars
- Total count calculation ambiguous: image count vs transcription count vs write count

**How to avoid:**
- **Centralize progress bar logic** or document lifecycle explicitly
- Create progress bar state machine: INIT → PROCESSING → WRITING → FINALIZING → DONE
- Define clear semantics: one `advance=1` per image processed, regardless of success/failure
- Audit all update sites: `grep -n "progress.update" transcribe.py`
- Document contract: "Progress bar counts IMAGES, not operations. Batch writing doesn't advance count."
- Test edge cases: empty batch, single image, error on first image, error on last image
- Add assertion: total advances equals image count at end

**Warning signs:**
- Progress bar total != number of images processed
- Progress bar gets "stuck" at certain points
- Progress bar advances twice for same image
- Progress bar shows >100% or <100% at completion
- Different behavior in LOCAL vs GOOGLECLOUD mode
- Writing operations advance progress (ambiguous: writing progress or processing progress?)

**Phase to address:**
Phase 2 (Progress bar fixes) - Must document lifecycle and verify advance count equals image count. Must test both modes and all error paths.

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Using `signal.SIGALRM` for timeouts | Simple, no threading complexity | Doesn't work on Windows, blocks porting | Never - cross-platform is core requirement |
| Monolithic 5,587-line script | No refactoring needed for bug fix | Hard to trace impact, difficult to test components in isolation | During rapid prototyping only, must refactor before v1.0 |
| Generic `except Exception` in retry logic | Catches all errors | Hides bugs, incorrect retry on non-retryable errors | Only in outermost try-except with explicit logging |
| Hardcoded buffer size (200 images) | Fast for typical use case | Fails on sparse numbering edge cases | Acceptable with documented limitation: "Max 200 image gap" |
| Return `None` on error (50+ sites) | Simpler than exception handling | Silent failures cascade, callers forget to check | Only for optional operations, never for critical paths |
| `advance=0` progress updates | Show status without changing count | Ambiguous semantics, easy to misuse | Acceptable with clear documentation: "advance=0 means status update only" |
| Mocking everything in tests | Tests run fast, no external dependencies | Tests don't catch real integration issues | Unit tests only, must have integration tests too |
| Single-platform development | Faster iteration, no VM setup | Platform-specific bugs ship to production | Early development only, must add CI matrix before beta |

## Integration Gotchas

Common mistakes when connecting to external services.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Google Drive API | Assuming list_images() is instantaneous for large folders | Implement pagination, add timeout, show progress for folder enumeration |
| Vertex AI API | Not handling per-minute rate limits (60 req/min) | Exponential backoff already implemented, but timeout must not trigger spurious retries |
| Google Docs API | Assuming batchUpdate is atomic | Check response, handle partial failures, implement idempotency |
| `threading.Timer` for timeout | Assuming timer cancellation is immediate | Call `timer.cancel()` AND handle race conditions where callback fires during cancel |
| `concurrent.futures` timeout | Assuming timed-out futures don't consume resources | Explicitly cancel futures, shut down executor, handle cleanup |
| Google OAuth | Token refresh during long-running process (>1hr) | Catch auth exceptions, retry with token refresh, don't assume credentials stay valid |

## Performance Traps

Patterns that work at small scale but fail as usage grows.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Fetching all images before filtering | List operation takes minutes, memory usage spikes | Use pagination, fetch in chunks, filter server-side if possible | >1000 images in folder |
| No timeout on folder enumeration | Drive API hangs indefinitely on large folders | Add timeout to list_images() call, not just transcription | >5000 images or slow network |
| Progress bar update per API call | Progress bar rendering becomes bottleneck | Batch progress updates, update every N items or every T seconds | >10,000 items |
| Synchronous API calls in timeout handler | Timeout fires but processing continues | Use cancellation tokens, check cancelled flag, exit early | Any timeout scenario |
| Linear retry backoff | Overwhelms API with retries | Use exponential backoff (already implemented: 60s → 120s → 300s) | Multiple concurrent failures |
| In-memory page accumulation | Memory grows unbounded with image count | Already mitigated with batch writing, but monitor memory usage | >500 images per batch |

## Security Mistakes

Domain-specific security issues beyond general web security.

| Mistake | Risk | Prevention |
|---------|------|------------|
| Logging full exception traceback | Credentials in exception messages leak to log files | Sanitize logs, redact patterns like `AIza.*`, `Bearer .*` tokens |
| Timeout exception contains API key | Debugging info includes full request with auth header | Sanitize exception messages before logging |
| Credentials in test fixtures | API keys hardcoded in test files committed to repo | Use environment variables, mock auth in tests |
| ADC file in repository root | Token refresh credentials committed to git | Already in .gitignore, but verify not in git history |
| Progress bar shows file paths | Leaks directory structure in terminal output | Acceptable risk for CLI tool, document if screensharing |

## UX Pitfalls

Common user experience mistakes in this domain.

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Progress bar "stuck" during batch write | User thinks script hung, kills process prematurely | Always update progress description: "Writing batch 3/10..." |
| Timeout error without retry indication | User doesn't know if retry is happening | Log: "Timeout on attempt 1/3, retrying with 2min timeout..." |
| Platform incompatibility discovered at runtime | Script crashes with cryptic error on Windows | Add startup check: detect Windows + signal usage, show clear error |
| Error after processing 100 images | Lost work, must restart from beginning | Already mitigated: log resume info, but document retry mode clearly |
| Generic "API Error" message | User can't diagnose or report issue | Include error code, rate limit info, retry recommendation |
| Progress bar shows 99% but actually done | User waits for non-existent last 1% | Verify progress bar total calculation includes all operations |

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **Cross-platform fix:** Test passes on macOS — verify manually on Windows
- [ ] **Timeout mechanism:** Works in happy path — verify behavior when timeout exhausted after all retries
- [ ] **Progress bar fix:** Counts correct in test — verify in both LOCAL and GOOGLECLOUD modes
- [ ] **Image buffer fix:** Works with sparse numbering — verify performance with 1000+ image folders
- [ ] **Error handling:** Logs error message — verify no credentials in log output
- [ ] **Integration test:** Uses mock with instant completion — verify with real delays/timeouts
- [ ] **Batch processing:** Works with 10 images — verify with 500 images, large batch size
- [ ] **Retry logic:** Retries on timeout — verify cleanup (no zombie threads, no continued API calls)
- [ ] **Mode compatibility:** Tested in LOCAL mode — verify GOOGLECLOUD mode still works
- [ ] **Config backward compatibility:** New code works with wizard config — verify works with legacy flat YAML

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Shipped Windows-incompatible fix | HIGH | Hotfix release, revert if needed, fast-track Windows testing to CI |
| Progress bar regression | LOW | Fix counts, verify with test suite, patch release |
| Timeout cleanup leak | MEDIUM | Add explicit cleanup code, test with stress scenario, review all threading patterns |
| New edge case from edge case fix | MEDIUM | Revert to buffer approach with increased size (500), document limitation |
| Incomplete test coverage | LOW | Add missing tests before next change, increase coverage threshold |
| Performance degradation | MEDIUM | Profile the slow operation, optimize or revert, add performance tests |
| Breaking change in bug fix | HIGH | Revert, create compatibility layer, version migration path |
| Lost backward compatibility | MEDIUM | Detect old config format, auto-migrate, document breaking change |

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Cross-platform incompatibility | Phase 1: Signal handling fix | CI runs on ubuntu/macos/windows matrix, manual Windows verification documented |
| Breaking existing functionality | Phase 2: Progress bar audit | Full regression test suite passes in both modes |
| Insufficient error path testing | Phase 4: Integration tests | Test explicitly verifies all-retries-exhausted scenario |
| New edge cases from fixes | Phase 3: Image buffer fix | Performance tested with 10/100/1000/5000 image folders |
| Test-induced damage | Phase 4: Test coverage | Mix of unit (mocked) + integration (real delays) + manual (platform-specific) |
| Progress bar lifecycle confusion | Phase 2: Progress bar fixes | Document lifecycle, verify advance count equals image count |
| Timeout cleanup | Phase 1: Signal handling fix | Verify no zombie threads after timeout, verify API call cancellation |
| Config compatibility break | All phases | Test with both wizard-generated and legacy flat YAML configs |

## Sources

**Project-specific:**
- `.planning/codebase/CONCERNS.md` - Known bugs and fragile areas
- `.planning/codebase/ARCHITECTURE.md` - Strategy pattern and component interactions
- `.planning/PROJECT.md` - Active requirements and out-of-scope items
- `transcribe.py:2812-2891` - Current signal-based timeout implementation
- `tests/unit/test_error_handling.py` - Current testing patterns
- `tests/unit/test_auth_strategies.py`, `test_ai_clients.py` - Strategy testing examples

**General Python bug fixing knowledge (HIGH confidence - based on well-established patterns):**
- Cross-platform Python development best practices (signal module platform limitations)
- Threading vs multiprocessing tradeoffs in Python
- Progress bar library patterns (tqdm, rich) and common pitfalls
- pytest best practices: unit vs integration testing
- Exception handling anti-patterns (bare except, return None)

**Medium confidence (project observation + Python ecosystem knowledge):**
- Monolithic codebases making impact analysis difficult (observed in this project)
- Strategy pattern testing challenges (observed test structure)
- Google API client error handling patterns (existing retry logic)

---
*Pitfalls research for: Python bug fixing (cross-platform, UI, edge cases)*
*Researched: 2026-02-21*
