# Business & Technical Analysis: Configuration Wizard & Context Separation

**Project:** Genea Metric Books Transcriber - Wizard Mode Configuration  
**Analysis Date:** January 2026  
**Phase:** Requirements & Analysis  
**Focus Area:** Configuration Experience & Context Management

---

## Executive Summary

This analysis evaluates the current configuration experience and proposes a wizard-based approach to eliminate YAML editing and separate context information (villages, surnames, archive details) from static prompt templates. The goal is to make prompt files static and immutable, while moving all project-specific context into a wizard-driven configuration system.

**Key Finding:** Current setup requires users to edit both YAML config files AND prompt markdown files, mixing static instructions with project-specific context. This creates maintenance burden, error-proneness, and prevents prompt template reuse.

**Target State:** Static prompt templates + Wizard-driven context collection + Automated prompt assembly = Zero manual file editing required.

**Adoption Impact:** Estimated current configuration time: 30-60 minutes per project. Target: 5-10 minutes with wizard guidance.

---

## Current State Assessment

### Configuration Pain Points

#### 1. Dual File Editing Requirement ⚠️ **CRITICAL**

**Current State:**
- Users must edit **two separate files** for each project:
  1. **YAML config file** (`config/config-*.yaml`) - 20+ parameters
  2. **Prompt markdown file** (`prompts/*.md`) - Contains both static instructions AND context

**Example from `prompts/f487o1s545-Turilche.md`:**
```markdown
# Context 

Державный Архив Тернопольской Области - Ф. 487, оп. 1, спр. 545 села Турилче...
Метрична книга про народження за 1888 (липень - грудень) - 1924...

## Villages: 
 Main related to document: 
    *   с. Турильче (v. Turilche, Turilcze)

May appear in document (not full list): 
    *   Вербивка (Werbivka, Werbowce...), 
    *   Нивра (Niwra, Нивра),
    ...

## Common Surnames in these villages:  
Boiechko (Боєчко), Voitkiv (Войтків), Havryliuk (Гаврилюк)...
```

**Problems:**
- Context (villages, surnames, archive info) is **hardcoded in prompt files**
- Each new project requires copying and editing a prompt file
- No separation between **static instructions** (transcription rules) and **dynamic context** (project data)
- Users must understand markdown syntax
- Risk of breaking prompt structure when editing context
- No validation of context completeness

**User Impact:**
- **Time to Complete:** 30-60 minutes per project
- **Error Rate:** Medium-High (estimated 30-40%)
- **Technical Knowledge Required:** Basic (markdown, YAML)
- **Support Burden:** Medium-High

---

#### 2. YAML Configuration Complexity ⚠️ **HIGH**

**Current State:**
- 20+ YAML parameters requiring manual editing
- Syntax errors (indentation, quotes) are common
- No interactive guidance
- Validation only at runtime

**Key Parameters:**
```yaml
mode: "local"  # or "googlecloud"
local:
  api_key: "..."
  image_dir: "..."
prompt_file: "f487o1s545-Turilche.md"  # Must match edited prompt file
archive_index: "ф487оп1спр545"
image_start_number: 1
image_count: 3
# ... 15+ more parameters
```

**Problems:**
- YAML syntax is error-prone (spaces vs tabs, quotes)
- No guided input (users must know valid values)
- Path validation only at runtime
- No pre-flight checks

**User Impact:**
- **Time to Complete:** 15-30 minutes per config
- **Error Rate:** Medium (estimated 25-30%)
- **Technical Knowledge Required:** Basic (YAML syntax)
- **Support Burden:** Medium

---

#### 3. Context Extraction from Title Page ⚠️ **MISSING OPPORTUNITY**

**Current State:**
- Title page images are specified in config (`title_page_filename`)
- Title pages often contain:
  - Archive reference (Ф. 487, оп. 1, спр. 545)
  - Village names
  - Date ranges
  - Document type
- **This information is NOT automatically extracted**

**Example Title Page Content:**
```
Державний архів Тернопільської області
Ф. 487, оп. 1, спр. 545
Метрична книга про народження
с. Турильче Борщівського повіту
1888 (липень - грудень) - 1924 (січень - квітень)
```

**Problems:**
- Users manually transcribe title page info into prompt file
- Duplication of effort (title page already scanned)
- Potential for transcription errors
- No automated context extraction

**Opportunity:**
- Use AI to extract context from title page image
- Pre-populate wizard fields
- Reduce manual data entry by 70-80%

---

#### 4. No Visual Feedback During Processing ⚠️ **MEDIUM**

**Current State:**
- Processing happens in terminal with file-based logging
- No progress indicators
- No real-time cost estimation
- Users don't know if process is frozen or working

**Problems:**
- Terminal output is not user-friendly
- No progress bars
- No time/cost estimates
- Difficult to gauge completion status

---

#### 5. No Pre-Flight Validation ⚠️ **MEDIUM**

**Current State:**
- Configuration errors discovered at runtime
- API failures happen after processing starts
- No validation of:
  - API key validity
  - Folder accessibility
  - Prompt file existence
  - Image file patterns

**Problems:**
- Wasted time and API calls
- Frustrating user experience
- Errors discovered too late

---

## Proposed Solution: Wizard Mode with Context Separation

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    WIZARD MODE                              │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │   Step 1:    │ -> │   Step 2:    │ -> │   Step 3:    │ │
│  │   Mode &     │    │   Context    │    │   Processing │ │
│  │   Source     │    │   Collection │    │   Settings   │ │
│  └──────────────┘    └──────────────┘    └──────────────┘ │
│         │                    │                    │         │
│         v                    v                    v         │
│  ┌──────────────────────────────────────────────────────┐ │
│  │         Context Extraction (Optional)                │ │
│  │  - Title Page OCR (if provided)                      │ │
│  │  - Auto-extract: archive ref, villages, dates        │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐ │
│  │         Prompt Assembly Engine                        │ │
│  │  - Load static template                              │ │
│  │  - Inject context from wizard                        │ │
│  │  - Generate final prompt                              │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐ │
│  │         Configuration Generation                      │ │
│  │  - Generate YAML config                              │ │
│  │  - Validate all settings                             │ │
│  │  - Pre-flight checks                                 │ │
│  └──────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## Solution Options

### Option A: Interactive CLI Wizard (Recommended - Quick Win)

**Approach:** Command-line wizard using `questionary` or `rich` libraries

**Features:**
1. **Step-by-Step Configuration:**
   ```
   $ python transcribe.py --wizard
   
   ┌─────────────────────────────────────────┐
   │  Genealogical Transcription Wizard     │
   └─────────────────────────────────────────┘
   
   Step 1/5: Select Mode
   [ ] Local (process images from folder)
   [x] Google Cloud (process from Drive folder)
   
   Step 2/5: Image Source
   Enter Google Drive folder URL: [________________]
   ✓ Extracted folder ID: 1e_T8TdXaWTYNfEQg-l8xX8Mhzm9IEF0T
   
   Step 3/5: Context Information
   Archive Reference: [ф487оп1спр545________]
   Main Village: [Турильче________________]
   Additional Villages (comma-separated): [Вербивка, Нивра__]
   Common Surnames (comma-separated): [Боєчко, Войтків, Гаврилюк...]
   
   Step 4/5: Title Page (Optional)
   [x] Extract context from title page
   Title page filename: [л. 000 обл...JPG]
   ✓ Extracted: Archive: Ф. 487, оп. 1, спр. 545
   ✓ Extracted: Village: Турильче
   ✓ Extracted: Date range: 1888-1924
   
   Step 5/5: Processing Settings
   Start image number: [1___]
   Number of images: [13__]
   Batch size: [3___]
   
   ✓ Configuration saved to: config/my-project.yaml
   ✓ Prompt template assembled
   ```

2. **Context Collection:**
   - Interactive prompts for villages, surnames, archive info
   - Optional title page OCR for auto-extraction
   - Validation and suggestions

3. **Prompt Assembly:**
   - Load static template (`prompts/templates/metric-book-birth.md`)
   - Inject context from wizard responses
   - Save assembled prompt (or use in-memory)

4. **Pre-Flight Validation:**
   - Check API key validity
   - Verify folder access
   - Validate image patterns
   - Test prompt assembly

**Pros:**
- ✅ No YAML editing required
- ✅ No prompt file editing required
- ✅ Guided, error-free input
- ✅ Quick to implement (3-5 days)
- ✅ Works with existing architecture
- ✅ Can extract context from title page

**Cons:**
- ⚠️ Still requires terminal/CLI
- ⚠️ Less visual than GUI

**Estimated Effort:** 3-5 days  
**Impact:** Very High - Eliminates 80% of configuration errors

---

### Option B: Web-Based Wizard (Long-Term)

**Approach:** Simple web application (Flask/FastAPI) with wizard interface

**Features:**
1. **Web UI with Multi-Step Form:**
   - Step 1: Mode selection (Local/Cloud)
   - Step 2: Image source configuration
   - Step 3: Context collection (with title page upload)
   - Step 4: Processing settings
   - Step 5: Review & generate

2. **Title Page Upload & OCR:**
   - Upload title page image
   - AI extracts context automatically
   - User reviews and corrects

3. **Visual Progress During Processing:**
   - Real-time progress bar
   - Current file being processed
   - Cost estimation
   - Time remaining

4. **HTML Proofing Output:**
   - Side-by-side image + transcription
   - Interactive verification
   - Export to Word/Docx

**Pros:**
- ✅ Most user-friendly
- ✅ Visual feedback
- ✅ No CLI knowledge required
- ✅ Can run on server (shared access)

**Cons:**
- ⚠️ Significant development effort (2-3 weeks)
- ⚠️ Requires hosting/deployment
- ⚠️ More complex architecture

**Estimated Effort:** 2-3 weeks  
**Impact:** Very High - Removes all technical barriers

---

### Option C: Hybrid Approach (Balanced)

**Approach:** CLI wizard + optional web dashboard

**Components:**
1. CLI wizard (as in Option A)
2. Optional web dashboard for:
   - Visual progress monitoring
   - HTML proofing output
   - Configuration management

**Pros:**
- ✅ Best of both worlds
- ✅ Serves power users and non-technical users
- ✅ Gradual migration path

**Cons:**
- ⚠️ Two interfaces to maintain

**Estimated Effort:** 1-2 weeks  
**Impact:** High - Covers both user types

---

## Context Separation Strategy

### Static Prompt Template Structure

**New Template Format (`prompts/templates/metric-book-birth.md`):**
```markdown
# Role
You are an expert archivist and paleographer specializing in 19th and early 20th-century Galician (Austrian/Polish/Ukrainian) 
vital records. Your task is to extract and transcribe handwritten text from the attached image of a metric book 
(birth, marriage, or death register).

# Context 

{{ARCHIVE_REFERENCE}}
{{DOCUMENT_DESCRIPTION}}
{{DATE_RANGE}}

## Villages: 
 Main related to document: 
{{MAIN_VILLAGES}}

May appear in document (not full list): 
{{ADDITIONAL_VILLAGES}}

## Common Surnames in these villages:  
{{COMMON_SURNAMES}}

# Instructions 
[... static instructions remain unchanged ...]
```

**Template Variables:**
- `{{ARCHIVE_REFERENCE}}` - Archive info (Ф. 487, оп. 1, спр. 545)
- `{{DOCUMENT_DESCRIPTION}}` - Document type and details
- `{{DATE_RANGE}}` - Date range (1888-1924)
- `{{MAIN_VILLAGES}}` - Primary village(s)
- `{{ADDITIONAL_VILLAGES}}` - Related villages
- `{{COMMON_SURNAMES}}` - Surname list

### Context Storage

**Option 1: Context in YAML Config (Recommended)**
```yaml
mode: "local"
local:
  api_key: "..."
  image_dir: "..."

# Context section (new)
context:
  archive_reference: "Державний архів Тернопільської області - Ф. 487, оп. 1, спр. 545"
  document_type: "Метрична книга про народження"
  date_range: "1888 (липень - грудень) - 1924 (січень - квітень)"
  main_villages:
    - name: "Турильче"
      variants: ["Turilche", "Turilcze"]
  additional_villages:
    - name: "Вербивка"
      variants: ["Werbivka", "Werbowce", "Wierzbówka", "Вербивці"]
    - name: "Нивра"
      variants: ["Niwra", "Нивра"]
  common_surnames:
    - "Boiechko (Боєчко)"
    - "Voitkiv (Войтків)"
    - "Havryliuk (Гаврилюк)"
    # ...

# Processing settings
prompt_template: "metric-book-birth"  # References static template
archive_index: "ф487оп1спр545"
image_start_number: 1
image_count: 3
```

**Option 2: Separate Context File**
```yaml
# config/my-project-context.yaml
archive_reference: "..."
villages: [...]
surnames: [...]
```

**Recommendation:** Store context in YAML config (Option 1) for simplicity and single-file configuration.

---

## Title Page Context Extraction

### Automated Extraction Flow

1. **User provides title page filename in wizard**
2. **Wizard loads title page image**
3. **AI extracts context using Gemini:**
   ```
   Extract from this title page image:
   - Archive reference (Ф. X, оп. Y, спр. Z)
   - Village names
   - Date range
   - Document type
   - Any other relevant metadata
   ```
4. **Wizard pre-populates fields with extracted data**
5. **User reviews and corrects if needed**

### Implementation

```python
def extract_context_from_title_page(image_path: str, api_key: str) -> dict:
    """
    Extract context information from title page image.
    
    Returns:
        {
            'archive_reference': 'Ф. 487, оп. 1, спр. 545',
            'main_villages': ['Турильче'],
            'date_range': '1888-1924',
            'document_type': 'Метрична книга про народження',
            ...
        }
    """
    extraction_prompt = """
    Extract the following information from this title page:
    1. Archive reference (Ф. X, оп. Y, спр. Z format)
    2. Village names mentioned
    3. Date range
    4. Document type
    5. Any other relevant metadata
    
    Return as structured JSON.
    """
    # Use Gemini to extract
    # Return structured data
```

**Benefits:**
- Reduces manual data entry by 70-80%
- More accurate than manual transcription
- Faster setup

---

## Visual Feedback & Progress Tracking

### Recommended Implementation

**Using `rich` library for CLI:**
```python
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.console import Console
from rich.panel import Panel

console = Console()

with Progress(
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}"),
    BarColumn(),
    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
    console=console,
) as progress:
    task = progress.add_task("Processing images...", total=image_count)
    
    for i, image in enumerate(images):
        # Process image
        progress.update(task, advance=1, description=f"Processing {image.name}")
        
        # Show cost estimate
        estimated_cost = calculate_cost(tokens_used)
        console.print(f"💰 Estimated cost: ${estimated_cost:.2f}")
```

**Features:**
- Progress bar with percentage
- Current file name
- Time elapsed / remaining
- Cost estimation (live calculation)
- Error indicators

---

## Pre-Flight Validation

### Validation Checklist

**Before processing starts, validate:**

1. **Authentication:**
   - [ ] API key exists and is valid (test with simple request)
   - [ ] Google Cloud credentials valid (if cloud mode)
   - [ ] Drive folder accessible (if cloud mode)

2. **Configuration:**
   - [ ] All required fields present
   - [ ] Image directory exists and is readable (if local mode)
   - [ ] Output directory is writable
   - [ ] Prompt template exists

3. **Context:**
   - [ ] Context data complete (villages, surnames provided)
   - [ ] Prompt assembly successful
   - [ ] Archive reference format valid

4. **Images:**
   - [ ] Image files found matching pattern
   - [ ] Image count matches expected range
   - [ ] Title page exists (if specified)

5. **Resources:**
   - [ ] API quota available
   - [ ] Sufficient disk space
   - [ ] Network connectivity

**Implementation:**
```python
def validate_configuration(config: dict) -> tuple[bool, list[str]]:
    """
    Pre-flight validation of configuration.
    
    Returns:
        (is_valid, list_of_errors)
    """
    errors = []
    
    # Validate authentication
    if not test_api_key(config['api_key']):
        errors.append("API key is invalid or expired")
    
    # Validate paths
    if not os.path.exists(config['image_dir']):
        errors.append(f"Image directory not found: {config['image_dir']}")
    
    # Validate context
    if not config.get('context', {}).get('main_villages'):
        errors.append("At least one main village must be specified")
    
    # ... more validations
    
    return len(errors) == 0, errors
```

---

## HTML Proofing Output

### Feature Description

**Generate HTML file alongside Word doc for quick verification:**

```html
<!DOCTYPE html>
<html>
<head>
    <style>
        .container {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        .image-panel {
            border: 1px solid #ccc;
            padding: 10px;
        }
        .transcription-panel {
            border: 1px solid #ccc;
            padding: 10px;
            font-family: monospace;
        }
        img {
            max-width: 100%;
            height: auto;
        }
    </style>
</head>
<body>
    <h1>Transcription Proofing: Image 001</h1>
    <div class="container">
        <div class="image-panel">
            <img src="image001.jpg" alt="Source image">
        </div>
        <div class="transcription-panel">
            <h2>Transcription</h2>
            <pre>[Transcribed text here]</pre>
        </div>
    </div>
</body>
</html>
```

**Benefits:**
- Fast to open (no Word required)
- Side-by-side comparison
- Easy to share/review
- Can be enhanced with interactive features

**Implementation:**
- Generate HTML file for each image or batch
- Include navigation between images
- Add verification checkboxes
- Export verified transcriptions

---

## Implementation Roadmap

### Phase 1: Core Wizard (Week 1)

**Deliverables:**
1. ✅ Interactive CLI wizard using `questionary`
2. ✅ Context collection (villages, surnames, archive info)
3. ✅ Static prompt template system
4. ✅ Prompt assembly engine
5. ✅ YAML config generation

**Effort:** 3-5 days  
**Impact:** High - Eliminates dual file editing

---

### Phase 2: Title Page Extraction (Week 2)

**Deliverables:**
1. ✅ Title page OCR integration
2. ✅ Context auto-extraction
3. ✅ Wizard pre-population
4. ✅ User review/correction interface

**Effort:** 2-3 days  
**Impact:** High - Reduces manual data entry by 70-80%

---

### Phase 3: Visual Feedback (Week 2-3)

**Deliverables:**
1. ✅ Progress bars using `rich`
2. ✅ Real-time cost estimation
3. ✅ Time remaining calculation
4. ✅ Error indicators

**Effort:** 2-3 days  
**Impact:** Medium - Better user experience

---

### Phase 4: Pre-Flight Validation (Week 3)

**Deliverables:**
1. ✅ Comprehensive validation function
2. ✅ Pre-flight checks before processing
3. ✅ Clear error messages with solutions
4. ✅ Auto-fix suggestions

**Effort:** 2-3 days  
**Impact:** High - Prevents runtime failures

---

### Phase 5: HTML Proofing (Week 3-4)

**Deliverables:**
1. ✅ HTML output generation
2. ✅ Side-by-side layout
3. ✅ Navigation between images
4. ✅ Export functionality

**Effort:** 2-3 days  
**Impact:** Medium - Faster verification workflow

---

## Success Metrics

### Current State
- **Configuration Time:** 30-60 minutes per project
- **Error Rate:** 30-40% (first attempt)
- **Files to Edit:** 2 (YAML + Prompt)
- **Technical Knowledge:** Basic (YAML, Markdown)
- **Context Extraction:** Manual (0% automated)

### Target State
- **Configuration Time:** 5-10 minutes per project
- **Error Rate:** <5% (first attempt)
- **Files to Edit:** 0 (wizard generates all)
- **Technical Knowledge:** Minimal (guided input)
- **Context Extraction:** 70-80% automated (from title page)

### Measurement
- Track wizard completion time
- Monitor error rates
- User feedback surveys
- Support ticket reduction

---

## Risk Assessment

### Technical Risks
- **Template System Complexity:** Prompt assembly must be robust
  - *Mitigation:* Comprehensive testing, fallback to manual prompts
- **Title Page OCR Accuracy:** May not extract all context correctly
  - *Mitigation:* Always allow user review/correction
- **Backward Compatibility:** Existing configs/prompts must still work
  - *Mitigation:* Wizard is optional, existing workflow unchanged

### User Adoption Risks
- **Learning Curve:** Users familiar with current process may resist change
  - *Mitigation:* Make wizard optional initially, provide migration guide
- **Template Limitations:** Static templates may not cover all use cases
  - *Mitigation:* Allow custom prompt templates, extensible system

---

## Recommendations

### Immediate Actions (Priority 1)

1. **Implement CLI Wizard (Option A)**
   - Highest impact, moderate effort
   - Eliminates dual file editing
   - Foundation for other improvements

2. **Create Static Prompt Templates**
   - Separate context from instructions
   - Enable template reuse
   - Reduce maintenance burden

3. **Add Context Section to YAML**
   - Store context in config
   - Enable prompt assembly
   - Single source of truth

### Short-Term (Priority 2)

4. **Title Page Context Extraction**
   - High value, moderate effort
   - Reduces manual work significantly

5. **Pre-Flight Validation**
   - Prevents user frustration
   - Catches errors early

### Medium-Term (Priority 3)

6. **Visual Feedback & Progress**
   - Better user experience
   - Reduces "is it frozen?" anxiety

7. **HTML Proofing Output**
   - Faster verification workflow
   - Better for genealogists

---

## Conclusion

The current configuration experience requires users to edit both YAML and Markdown files, mixing static instructions with project-specific context. This creates unnecessary complexity and error-proneness.

**Recommended Solution:**
- **Phase 1:** CLI Wizard + Static Templates + Context Separation (Week 1)
- **Phase 2:** Title Page Extraction (Week 2)
- **Phase 3:** Visual Feedback + Validation + HTML Proofing (Week 3-4)

**Expected Outcome:**
- Configuration time: 30-60 min → 5-10 min
- Error rate: 30-40% → <5%
- Files to edit: 2 → 0
- User satisfaction: Significantly improved

---

**Document Version:** 1.0  
**Last Updated:** January 2026  
**Next Review:** After Phase 1 implementation
