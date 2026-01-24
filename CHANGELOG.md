# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v0.4-beta-dual-mode] - 2026-01-24

### Added

#### Multi-Format Output for LOCAL Mode
- **Markdown Output**: Structured markdown files saved in source image directory
  - Session overview with metadata
  - Formatted transcriptions with proper newlines
  - Source image links (relative paths)
- **Word Document Output**: Microsoft Word (.docx) files with formatted transcriptions
  - Bold text formatting for emphasized terms
  - Page-numbered headers (e.g., ф487оп1спр545-стр1)
  - Session metadata and overview
- **Composite Output Pattern**: Multiple output formats generated simultaneously
  - Log files (in output_dir)
  - Markdown files (in image_dir)
  - Word documents (in image_dir)

#### Enhanced Error Handling
- Retry logic with exponential backoff for 503 ServerError in LOCAL mode
- Improved error messages with human-friendly descriptions
- Resume instructions in output documents on errors
- Partial results saved even when errors occur

#### Windows Compatibility
- Cross-platform path handling for file:// URLs
- Normalized path separators for Windows compatibility
- Relative path links in Markdown output to prevent path duplication

#### Documentation
- Detailed OAuth authentication instructions using refresh_credentials.py
- Step-by-step guide for creating OAuth 2.0 clients in Google Cloud Console
- Updated Ukrainian documentation (README-UKRAINIAN.md)
- Enhanced authentication method documentation

### Fixed

- Fixed duplicate document creation in GOOGLECLOUD mode
- Fixed empty range styling errors in Google Docs API calls
- Fixed config access for nested configuration format in GOOGLECLOUD mode
- Fixed path duplication in Markdown source links (LOCAL mode)
- Fixed 503 Service Unavailable error handling with proper retry logic
- Fixed Windows file:// URL path normalization

### Changed

- Improved error handling to ensure output documents are always finalized
- Enhanced logging with full prompt text at session start
- Better error context preservation in exception handling

## [v0.3-beta-local] - 2026-01-24

### Added

#### LOCAL Mode (Tested and Certified)
- Complete LOCAL mode implementation
- Multi-format output (Log, Markdown, Word)
- Windows compatibility fixes
- Comprehensive error handling

## [v0.3-beta] - 2026-01-24

### Added

#### Dual-Mode Operation
- **LOCAL Mode**: New mode for processing images from local file system
  - No Google Cloud setup required - just need Gemini API key
  - Outputs transcriptions to log files
  - Simpler setup and faster iteration
  - See `config/config.local.example.yaml` for configuration

- **GOOGLECLOUD Mode**: Enhanced original functionality
  - Improved configuration structure
  - Better error handling and validation
  - All original features preserved

#### Configuration System
- New nested configuration format with explicit mode selection
- Automatic mode detection from configuration
- Backward compatibility with legacy flat configuration format
- Configuration validation with clear error messages
- Environment variable support for API keys (`GEMINI_API_KEY`)

#### Strategy Pattern Architecture
- Refactored codebase using Strategy pattern for better maintainability
- Separate strategies for:
  - Authentication (LocalAuthStrategy, GoogleCloudAuthStrategy)
  - Image Sources (LocalImageSource, DriveImageSource)
  - AI Clients (GeminiDevClient, VertexAIClient)
  - Output (LogFileOutput, GoogleDocsOutput)
- ModeFactory for creating mode-specific handlers

#### Testing & Quality
- Comprehensive test suite: 82 tests covering unit, integration, compatibility, performance, and error handling
- Memory-optimized test execution
- Test coverage for all strategy classes
- Backward compatibility tests for legacy configurations

#### Documentation
- Updated README with dual-mode documentation
- New Configuration Guide (`docs/CONFIGURATION.md`)
- New Migration Guide (`docs/MIGRATION.md`)
- Memory optimization documentation (`MEMORY_OPTIMIZATION.md`)
- Example configurations for both modes

### Changed

#### Configuration Format
- **Breaking Change (Optional)**: New nested configuration format recommended
  - Legacy format still supported for backward compatibility
  - See [Migration Guide](docs/MIGRATION.md) for details
  - Old configs continue to work without changes

#### Error Handling
- Improved error messages with mode-specific guidance
- Better validation feedback
- Clearer troubleshooting information

#### Code Structure
- Refactored main processing logic into mode-specific functions
- Improved code organization and maintainability
- Better separation of concerns

### Fixed

- Improved retry logic with exponential backoff for API calls
- Better handling of API timeouts and connection errors
- Fixed memory issues in test execution
- Improved error recovery and resume functionality

### Security

- Support for environment variables for sensitive data (API keys)
- Recommendations for secure credential management

### Performance

- Memory-optimized test execution
- Improved test execution speed
- Better resource cleanup

## [v0.2-beta] - Pre-Dual-Mode

### Features

- Google Drive integration for image sources
- Vertex AI Gemini for transcription
- Google Docs output with formatted transcriptions
- Batch processing with incremental document writing
- Retry mechanism for failed images
- Recovery script for rebuilding documents from logs
- Comprehensive logging system
- Support for multiple filename patterns
- Archive index references
- Title page image support

---

## Migration Notes

### Upgrading from v0.3-beta to v0.4-beta-dual-mode

**New Features:**
- Multi-format output in LOCAL mode (Markdown and Word files)
- Enhanced error handling with retry logic for 503 errors
- Windows compatibility improvements
- Improved OAuth authentication documentation

**No breaking changes** - all existing configurations continue to work.

### Upgrading from v0.2-beta to v0.3-beta

**Your existing configuration files will continue to work!** The tool automatically detects and converts legacy configs.

**Recommended**: Migrate to the new configuration format for:
- Clearer structure
- Access to LOCAL mode
- Better validation
- Future-proof setup

See [Migration Guide](docs/MIGRATION.md) for detailed instructions.

### Key Changes

1. **New Configuration Format** (optional):
   - Legacy format still supported
   - New nested format recommended
   - Automatic conversion for legacy configs

2. **New LOCAL Mode**:
   - Requires Gemini API key (get from [Google AI Studio](https://aistudio.google.com/app/apikey))
   - No Google Cloud setup needed
   - Outputs to log files instead of Google Docs

3. **Improved Error Handling**:
   - Better error messages
   - Mode-specific troubleshooting
   - Clearer validation feedback

### Breaking Changes

**None** - The tool maintains full backward compatibility with existing configurations and workflows.

---

## Version History

- **v0.4-beta-dual-mode** (2026-01-24): Multi-format output, enhanced error handling, Windows compatibility, OAuth documentation
- **v0.3-beta-local** (2026-01-24): Tested and certified LOCAL mode with multi-format output
- **v0.3-beta** (2026-01-24): Dual-mode operation, strategy pattern refactoring, comprehensive testing
- **v0.2-beta** (Pre-2026): Google Cloud integration release
- **v0.1-beta** (Pre-2026): Initial release
