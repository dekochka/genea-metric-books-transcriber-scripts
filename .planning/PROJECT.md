# GeneA Transcriber - Bug Fixes & Quality Improvement

## What This Is

A Python CLI tool for batch-processing genealogy document images using Google's Gemini AI for OCR and transcription. Operates in two modes: LOCAL (processes local files, outputs to markdown/Word) and GOOGLECLOUD (processes from Google Drive, outputs to Google Docs). This cleanup milestone addresses known bugs and test coverage gaps to establish a stable foundation before adding new features.

## Core Value

Reliable cross-platform batch transcription of genealogy documents. If the tool can't consistently process images without crashing or producing incorrect output, everything else is irrelevant.

## Requirements

### Validated

<!-- Shipped and confirmed valuable from existing codebase -->

- ✓ Dual-mode operation (LOCAL and GOOGLECLOUD) - existing
- ✓ Strategy pattern for pluggable auth, image sources, AI clients, and outputs - existing
- ✓ Wizard-based interactive configuration with AI-powered context extraction - existing
- ✓ Batch processing with configurable batch sizes - existing
- ✓ Retry logic with exponential backoff for API failures - existing
- ✓ Multiple output formats (log files, markdown, Word docs, Google Docs) - existing
- ✓ Comprehensive logging with dual logger setup (main + AI responses) - existing
- ✓ Cost calculation and metrics tracking - existing
- ✓ Configuration validation and migration from legacy formats - existing

### Active

<!-- Current scope: Bug fixes and test coverage -->

- [ ] Platform-agnostic timeout mechanism (replace Unix-only signal.SIGALRM with threading.Timer or concurrent.futures)
- [ ] Accurate progress bar counts during document writing operations
- [ ] Robust image fetching for sparse filename numbering (fetch all images, then filter)
- [ ] Test coverage for cross-platform signal timeout mechanism
- [ ] Test coverage for progress bar edge cases (batch writing, finalization)
- [ ] Test coverage for image buffer edge cases (sparse numbering, large gaps)
- [ ] Integration test verifying timeout behavior when all retries exhausted
- [ ] Manual verification on Windows platform for signal handling fix

### Out of Scope

- Performance improvements (parallel processing, caching) — deferred to future milestone
- Security hardening (credential storage, log sanitization) — deferred to future milestone
- Tech debt reduction (monolithic file refactoring, exception handling improvements) — deferred to future milestone
- Missing critical features (resume/checkpoint, batch job management, additional output formats) — deferred to future milestone
- Test coverage for wizard mode edge cases — not critical for bug fix milestone

## Context

**Existing Architecture:**
- Monolithic 5,587-line `transcribe.py` with strategy pattern implementation
- Plugin-style wizard subsystem for interactive configuration
- Dual-mode operation: LOCAL (developer API + local files) vs GOOGLECLOUD (Vertex AI + Drive/Docs)
- Comprehensive test suite in `tests/unit/` and `tests/integration/` with pytest

**Known Issues Addressed:**
- **Signal handling (CRITICAL)**: Current Unix-only `signal.SIGALRM` timeout mechanism crashes on Windows
- **Progress bars (UX)**: Recent fix in v0.5-beta-wizard-mode may have edge cases in document finalization
- **Image buffer (EDGE CASE)**: 200-image buffer insufficient for very sparse filename numbering patterns

**Quality Goals:**
This milestone focuses on reliability and cross-platform compatibility. The goal is to establish a stable, well-tested foundation before tackling larger refactoring efforts or new features.

## Constraints

- **Platform compatibility**: Must work on both Unix (macOS, Linux) and Windows
- **Backward compatibility**: Fixes must not break existing configuration files or workflows
- **Minimal API changes**: Keep strategy interfaces unchanged to avoid cascading changes
- **Testing standard**: All bug fixes must include automated tests proving the fix

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Use threading.Timer for timeouts | Cross-platform compatible, simpler than concurrent.futures for this use case | — Pending |
| Fix progress bars in-place | Avoid refactoring output strategies during bug fix milestone | — Pending |
| Fetch all images for range selection | More robust than buffer-based approach, acceptable performance trade-off | — Pending |
| Prioritize manual Windows verification | Signal handling is critical bug affecting entire Windows user base | — Pending |

---
*Last updated: 2026-02-21 after initialization*
