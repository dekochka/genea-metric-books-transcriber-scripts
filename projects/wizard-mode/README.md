# Wizard Mode Configuration Project

## Overview

This project focuses on improving the configuration experience by introducing an interactive wizard that eliminates the need for manual YAML and prompt file editing. The key innovation is separating static prompt instructions from project-specific context (villages, surnames, archive info).

## Project Goals

1. **Eliminate Dual File Editing**: Users currently must edit both YAML config files AND prompt markdown files
2. **Separate Context from Instructions**: Make prompt templates static and immutable, move context to wizard/config
3. **Automate Context Extraction**: Extract context from title page images when provided
4. **Improve User Experience**: Add visual feedback, pre-flight validation, and HTML proofing output

## Project Structure

```
projects/wizard-mode/
├── README.md                              # This file
├── 01-analysis-configuration-wizard.md   # Business & technical analysis
├── 02-technical-design.md                # (Future) Technical design document
├── 03-implementation-plan.md             # (Future) Detailed implementation plan
└── 04-implementation-progress.md         # (Future) Progress tracking
```

## Key Documents

### 01-analysis-configuration-wizard.md

Comprehensive analysis document covering:
- Current state assessment and pain points
- Proposed solution options (CLI wizard, web-based, hybrid)
- Context separation strategy
- Title page context extraction
- Visual feedback & progress tracking
- Pre-flight validation
- HTML proofing output
- Implementation roadmap
- Success metrics and risk assessment

### 02-technical-design.md

Detailed technical design specification covering:
- System architecture and component design
- Data structures and API specifications
- Integration points with existing codebase
- File structure and dependencies
- Implementation details for each component
- Error handling and testing strategy
- Backward compatibility approach
- Implementation phases and success criteria

### 03-implementation-plan.md

Detailed implementation plan with:
- Phase-by-phase breakdown (8 phases)
- Specific tasks with time estimates
- Dependencies and acceptance criteria
- Risk mitigation strategies
- Testing and documentation requirements
- Deployment plan

### 04-implementation-progress.md

Progress tracking document with:
- Overall progress status
- Phase-by-phase status tracking
- Task completion checklists
- Blockers and issues log
- Decisions made
- Metrics tracking

## Static Prompt Templates

Static templates have been created in `prompts/templates/`:
- `metric-book-birth.md` - Template for metric book birth records (based on Turilche example)

Templates use placeholder variables (e.g., `{{ARCHIVE_REFERENCE}}`, `{{MAIN_VILLAGES}}`) that are replaced with context data collected through the wizard.

## Next Steps

1. **Review Analysis**: Stakeholder review of `01-analysis-configuration-wizard.md`
2. **Select Approach**: Choose between CLI wizard (Option A), web-based (Option B), or hybrid (Option C)
3. **Create Technical Design**: Detailed design document for selected approach
4. **Implementation**: Begin Phase 1 (Core Wizard) development

## Related Projects

- `projects/app-install-simplification/` - Previous project focused on ease of setup and Local mode introduction

## Status

**Current Phase:** Implementation Plan Complete  
**Next Phase:** Development - Phase 0 (Preparation & Setup)

---

**Last Updated:** January 2026
