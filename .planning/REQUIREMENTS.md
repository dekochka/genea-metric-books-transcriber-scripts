# Requirements: GeneA Transcriber - Bug Fixes & Quality Improvement

**Defined:** 2026-02-21
**Core Value:** Reliable cross-platform batch transcription of genealogy documents

## v1 Requirements

Requirements for bug fix milestone. Each maps to roadmap phases.

### Signal Handling (Cross-Platform Compatibility)

- [x] **SIGNAL-01**: Replace signal.SIGALRM with threading.Timer in VertexAIClient retry logic
- [x] **SIGNAL-02**: Preserve exponential backoff timing (60s, 120s, 300s) across all timeout attempts
- [x] **SIGNAL-03**: Handle TimeoutError exceptions consistently with existing retry mechanism
- [x] **SIGNAL-04**: Clean up timer resources on both success and failure paths
- [ ] **SIGNAL-05**: Add unit test verifying timeout fires correctly after specified duration
- [ ] **SIGNAL-06**: Add unit test verifying timer cancels on successful API response
- [ ] **SIGNAL-07**: Add integration test for retry logic with timeout on first attempt
- [ ] **SIGNAL-08**: Add integration test for all retries exhausted scenario
- [ ] **SIGNAL-09**: Run tests on Windows platform (CI or manual VM verification)
- [ ] **SIGNAL-10**: Verify no AttributeError on Windows when importing/running application

### Progress Bar Accuracy

- [ ] **PROGRESS-01**: Audit all progress.update() call sites across transcribe.py and output strategies
- [ ] **PROGRESS-02**: Document progress bar lifecycle state machine (INIT → PROCESSING → WRITING → FINALIZING → DONE)
- [ ] **PROGRESS-03**: Fix progress count logic in LogFileOutput.finalize()
- [ ] **PROGRESS-04**: Fix progress count logic in GoogleDocsOutput.finalize()
- [ ] **PROGRESS-05**: Fix progress count logic in MarkdownOutput.finalize()
- [ ] **PROGRESS-06**: Fix progress count logic in WordOutput.finalize()
- [ ] **PROGRESS-07**: Fix progress count logic in CompositeOutput.finalize()
- [ ] **PROGRESS-08**: Ensure total advances equals image count at completion for LOCAL mode
- [ ] **PROGRESS-09**: Ensure total advances equals image count at completion for GOOGLECLOUD mode
- [ ] **PROGRESS-10**: Add unit tests for each OutputStrategy.finalize() with edge cases (0, 1, batch boundary images)
- [ ] **PROGRESS-11**: Add integration test verifying progress updates during batch write operations
- [ ] **PROGRESS-12**: Add integration test for progress behavior during error/retry scenarios
- [ ] **PROGRESS-13**: Manual visual verification of progress bar rendering with 100+ images
- [ ] **PROGRESS-14**: Verify progress bar accuracy in both LOCAL and GOOGLECLOUD modes end-to-end

### Image Buffer Robustness

- [ ] **BUFFER-01**: Replace 200-image buffer logic with fetch-all-then-filter approach in DriveImageSource.list_images()
- [ ] **BUFFER-02**: Preserve list_images() interface signature (no breaking changes)
- [ ] **BUFFER-03**: Handle sparse filename numbering patterns (gaps of 10, 100, 500 between image numbers)
- [ ] **BUFFER-04**: Implement pagination for folders with 1000+ images to avoid Drive API timeouts
- [ ] **BUFFER-05**: Add unit test for sparse numbering patterns (e.g., img_0500, img_0520, img_0700)
- [ ] **BUFFER-06**: Add unit test for contiguous numbering pattern
- [ ] **BUFFER-07**: Add unit test for single image in folder
- [ ] **BUFFER-08**: Add unit test for empty folder
- [ ] **BUFFER-09**: Add performance test asserting <30s fetch time for 1000-image folder
- [ ] **BUFFER-10**: Add integration test with mocked Drive API returning paginated sparse results
- [ ] **BUFFER-11**: Verify backward compatibility with existing config files
- [ ] **BUFFER-12**: Verify no memory issues with large image lists (5000+ images)

### Integration Testing & CI

- [ ] **CI-01**: Set up GitHub Actions workflow with platform matrix (ubuntu-latest, macos-latest, windows-latest)
- [ ] **CI-02**: Configure pytest markers for test categorization (unit, integration, windows, unix, timeout, progress, edge_case)
- [ ] **CI-03**: Add integration test for signal handling with mocked slow API and timeout trigger
- [ ] **CI-04**: Add integration test for progress bars with actual batch output writing
- [ ] **CI-05**: Add integration test for image buffer with mocked Drive API sparse results
- [ ] **CI-06**: Add end-to-end integration test processing 100 images in LOCAL mode
- [ ] **CI-07**: Add end-to-end integration test processing 100 images in GOOGLECLOUD mode
- [ ] **CI-08**: Verify full regression test suite passes on all three platforms
- [ ] **CI-09**: Add manual testing checklist for Windows-specific verification
- [ ] **CI-10**: Document CI setup and platform testing requirements in README

### Quality & Documentation

- [ ] **QUALITY-01**: Add changelog entries for all three bug fixes with clear user impact description
- [ ] **QUALITY-02**: Verify backward compatibility with legacy flat YAML config format
- [ ] **QUALITY-03**: Verify backward compatibility with new wizard-generated hierarchical config format
- [x] **QUALITY-04**: Document threading.Timer timeout mechanism in code comments
- [ ] **QUALITY-05**: Document progress bar state machine in inline comments
- [ ] **QUALITY-06**: Update README with Windows compatibility confirmation
- [ ] **QUALITY-07**: Run full regression test suite in both LOCAL and GOOGLECLOUD modes
- [ ] **QUALITY-08**: Achieve 80%+ code coverage for changed files
- [ ] **QUALITY-09**: Verify no new linting warnings or errors introduced
- [ ] **QUALITY-10**: Update version number and prepare release notes

## v2 Requirements

Deferred tech debt and enhancements not in current bug fix scope.

### Performance Improvements
- **PERF-01**: Parallel image processing with concurrent.futures.ThreadPoolExecutor
- **PERF-02**: Image caching to disk to avoid re-downloading on retry
- **PERF-03**: Exponential backoff with jitter for rate limiting in recovery script
- **PERF-04**: Single-pass cost calculation during metrics collection

### Tech Debt Reduction
- **DEBT-01**: Refactor monolithic 5,587-line transcribe.py into modular architecture
- **DEBT-02**: Replace bare exception handlers with specific exception types
- **DEBT-03**: Replace return None patterns with exceptions or Result types
- **DEBT-04**: Extract recovery script shared logic into reusable libraries
- **DEBT-05**: Define specific exception types for strategy failures

### Security Hardening
- **SEC-01**: Move credential files outside repository to ~/.config/genea-transcriber/
- **SEC-02**: Sanitize exception messages before logging to prevent credential leakage
- **SEC-03**: Add log filter to redact API key patterns from output
- **SEC-04**: Integrate with system keychains for secure credential storage

### Missing Critical Features
- **FEAT-01**: Resume/checkpoint capability for large processing jobs
- **FEAT-02**: Batch job queue management for overnight processing
- **FEAT-03**: PDF export output format using reportlab
- **FEAT-04**: DOCX file output format finalization
- **FEAT-05**: Audit trail embedding AI metadata in output documents

## Out of Scope

| Feature | Reason |
|---------|--------|
| Refactoring monolithic file structure | High risk during bug fix milestone, defer to dedicated refactoring phase |
| Performance optimizations | Not blocking bugs, defer to performance-focused milestone |
| Security credential improvements | No active security incidents, defer to security-focused milestone |
| Additional output formats | Feature additions out of scope for bug fix milestone |
| Wizard mode edge case improvements | Test coverage gap but not causing production issues |
| Recovery script modernization | Nice-to-have but not blocking current workflows |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| SIGNAL-01 | Phase 1 | Complete |
| SIGNAL-02 | Phase 1 | Complete |
| SIGNAL-03 | Phase 1 | Complete |
| SIGNAL-04 | Phase 1 | Complete |
| SIGNAL-05 | Phase 1 | Pending |
| SIGNAL-06 | Phase 1 | Pending |
| SIGNAL-07 | Phase 1 | Pending |
| SIGNAL-08 | Phase 1 | Pending |
| SIGNAL-09 | Phase 1 | Pending |
| SIGNAL-10 | Phase 1 | Pending |
| BUFFER-01 | Phase 2 | Pending |
| BUFFER-02 | Phase 2 | Pending |
| BUFFER-03 | Phase 2 | Pending |
| BUFFER-04 | Phase 2 | Pending |
| BUFFER-05 | Phase 2 | Pending |
| BUFFER-06 | Phase 2 | Pending |
| BUFFER-07 | Phase 2 | Pending |
| BUFFER-08 | Phase 2 | Pending |
| BUFFER-09 | Phase 2 | Pending |
| BUFFER-10 | Phase 2 | Pending |
| BUFFER-11 | Phase 2 | Pending |
| BUFFER-12 | Phase 2 | Pending |
| PROGRESS-01 | Phase 3 | Pending |
| PROGRESS-02 | Phase 3 | Pending |
| PROGRESS-03 | Phase 3 | Pending |
| PROGRESS-04 | Phase 3 | Pending |
| PROGRESS-05 | Phase 3 | Pending |
| PROGRESS-06 | Phase 3 | Pending |
| PROGRESS-07 | Phase 3 | Pending |
| PROGRESS-08 | Phase 3 | Pending |
| PROGRESS-09 | Phase 3 | Pending |
| PROGRESS-10 | Phase 3 | Pending |
| PROGRESS-11 | Phase 3 | Pending |
| PROGRESS-12 | Phase 3 | Pending |
| PROGRESS-13 | Phase 3 | Pending |
| PROGRESS-14 | Phase 3 | Pending |
| CI-01 | Phase 4 | Pending |
| CI-02 | Phase 4 | Pending |
| CI-03 | Phase 4 | Pending |
| CI-04 | Phase 4 | Pending |
| CI-05 | Phase 4 | Pending |
| CI-06 | Phase 4 | Pending |
| CI-07 | Phase 4 | Pending |
| CI-08 | Phase 4 | Pending |
| CI-09 | Phase 4 | Pending |
| CI-10 | Phase 4 | Pending |
| QUALITY-01 | Phase 4 | Pending |
| QUALITY-02 | Phase 4 | Pending |
| QUALITY-03 | Phase 4 | Pending |
| QUALITY-04 | Phase 1 | Complete |
| QUALITY-05 | Phase 3 | Pending |
| QUALITY-06 | Phase 4 | Pending |
| QUALITY-07 | Phase 4 | Pending |
| QUALITY-08 | Phase 4 | Pending |
| QUALITY-09 | Phase 4 | Pending |
| QUALITY-10 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 56 total
- Mapped to phases: 56
- Unmapped: 0 ✓

---
*Requirements defined: 2026-02-21*
*Last updated: 2026-02-21 after initial definition*
