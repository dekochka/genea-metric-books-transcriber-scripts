# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

- **v0.3-beta** (2026-01-24): Dual-mode operation, strategy pattern refactoring, comprehensive testing
- **v0.2-beta** (Pre-2026): Google Cloud integration release
- **v0.1-beta** (Pre-2026): Initial release
