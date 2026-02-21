# Roadmap: GeneA Transcriber - Bug Fixes & Quality Improvement

**Project:** Reliable cross-platform batch transcription of genealogy documents
**Milestone:** Bug fix and quality improvement milestone
**Depth:** Standard
**Total Phases:** 4

## Phases

- [x] **Phase 1: Cross-Platform Timeout Fix** - Replace Unix-only signal.SIGALRM with threading.Timer
- [ ] **Phase 2: Image Buffer Robustness** - Handle sparse filename numbering with fetch-all-then-filter
- [ ] **Phase 3: Progress Bar Lifecycle Audit** - Fix progress count logic across all output strategies
- [ ] **Phase 4: Integration Testing & CI** - Establish cross-platform CI and comprehensive test coverage

## Phase Details

### Phase 1: Cross-Platform Timeout Fix
**Goal**: Windows users can run the transcription tool without AttributeError crashes

**Depends on**: Nothing (first phase)

**Requirements**: SIGNAL-01, SIGNAL-02, SIGNAL-03, SIGNAL-04, SIGNAL-05, SIGNAL-06, SIGNAL-07, SIGNAL-08, SIGNAL-09, SIGNAL-10, QUALITY-04

**Success Criteria** (what must be TRUE):
1. Tool imports successfully on Windows without AttributeError from signal.SIGALRM
2. Timeout mechanism triggers after specified duration (60s, 120s, 300s) across all retry attempts
3. Timer cancels cleanly when API response arrives before timeout
4. Retry logic preserves exponential backoff behavior unchanged from signal-based implementation
5. Thread resources are cleaned up on both success and failure code paths

**Plans**: 4 plans in 4 waves

Plans:
- [x] 01-01-PLAN.md — Implement TimeoutContext class and replace signal-based timeout
- [x] 01-02-PLAN.md — Add test dependencies and create unit/integration tests for timeout mechanism
- [x] 01-03-PLAN.md — Create Windows platform tests and GitHub Actions CI workflow
- [x] 01-04-PLAN.md — Document verification approach and trust rationale for Windows compatibility

---

### Phase 2: Image Buffer Robustness
**Goal**: Users can process folders with sparse filename numbering patterns without missing images

**Depends on**: Nothing (parallel with Phase 1)

**Requirements**: BUFFER-01, BUFFER-02, BUFFER-03, BUFFER-04, BUFFER-05, BUFFER-06, BUFFER-07, BUFFER-08, BUFFER-09, BUFFER-10, BUFFER-11, BUFFER-12

**Success Criteria** (what must be TRUE):
1. Tool correctly identifies and processes images with large gaps in numbering (e.g., img_0500, img_0520, img_0700)
2. DriveImageSource.list_images() handles folders with 1000+ images without Drive API timeouts
3. Existing configuration files continue to work without modification
4. Performance remains acceptable (folder enumeration completes in <30s for 1000 images)

**Plans**: TBD

---

### Phase 3: Progress Bar Lifecycle Audit
**Goal**: Progress bar accurately reflects work completed during all stages of processing

**Depends on**: Phase 1, Phase 2 (benefits from established test patterns)

**Requirements**: PROGRESS-01, PROGRESS-02, PROGRESS-03, PROGRESS-04, PROGRESS-05, PROGRESS-06, PROGRESS-07, PROGRESS-08, PROGRESS-09, PROGRESS-10, PROGRESS-11, PROGRESS-12, PROGRESS-13, PROGRESS-14, QUALITY-05

**Success Criteria** (what must be TRUE):
1. Total progress advances equals image count at completion for both LOCAL and GOOGLECLOUD modes
2. Progress bar updates correctly during batch write operations across all output strategies
3. Progress bar shows accurate counts at all lifecycle stages (INIT → PROCESSING → WRITING → FINALIZING → DONE)
4. Edge cases handled correctly (0 images, 1 image, batch boundary counts)
5. Visual inspection confirms smooth progress rendering with 100+ images

**Plans**: TBD

---

### Phase 4: Integration Testing & CI
**Goal**: All bug fixes validated across platforms with automated regression prevention

**Depends on**: Phase 1, Phase 2, Phase 3 (validates all completed fixes)

**Requirements**: CI-01, CI-02, CI-03, CI-04, CI-05, CI-06, CI-07, CI-08, CI-09, CI-10, QUALITY-01, QUALITY-02, QUALITY-03, QUALITY-06, QUALITY-07, QUALITY-08, QUALITY-09, QUALITY-10

**Success Criteria** (what must be TRUE):
1. GitHub Actions CI runs full test suite on ubuntu-latest, macos-latest, and windows-latest
2. Integration tests verify end-to-end workflows for all three bug fixes with realistic scenarios
3. Full regression test suite passes on all three platforms
4. Code coverage meets 80%+ threshold for changed files
5. README confirms Windows compatibility and changelog documents all bug fixes

**Plans**: TBD

---

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Cross-Platform Timeout Fix | 4/4 | Complete    | 2026-02-21 |
| 2. Image Buffer Robustness | 0/? | Not started | - |
| 3. Progress Bar Lifecycle Audit | 0/? | Not started | - |
| 4. Integration Testing & CI | 0/? | Not started | - |

## Requirement Coverage

**Total v1 requirements:** 56
**Requirements mapped to phases:** 56
**Orphaned requirements:** 0 ✓

### Coverage Map

| Phase | Requirement Count | Categories |
|-------|-------------------|------------|
| Phase 1 | 11 | Signal Handling (10), Quality (1) |
| Phase 2 | 12 | Image Buffer (12) |
| Phase 3 | 15 | Progress Bar (14), Quality (1) |
| Phase 4 | 18 | CI & Integration (10), Quality (8) |

## Phase Dependencies

```
Phase 1 (Critical blocker)
  ↓
Phase 2 (Parallel with Phase 1)
  ↓
Phase 3 (Requires test patterns from 1-2)
  ↓
Phase 4 (Validates all fixes)
```

## Notes

**Parallel work opportunities:**
- Phase 1 and Phase 2 can proceed independently
- Phase 4 CI setup can begin during Phase 1 (needed for Windows testing)

**Risk mitigation:**
- Highest-impact bug (Windows crash) fixed first in Phase 1
- Each phase is independently testable with clear success criteria
- Progressive complexity: clear stdlib fix → isolated edge case → multi-component audit → full integration

---
*Roadmap created: 2026-02-21*
*Phase 1 planned: 2026-02-21*
*Next action: `/gsd:execute-phase 1`*
