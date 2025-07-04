# 📦 Willow Changelog

## [v5.1.1] – 2025-07-04

### Added

- Gemini 2.5 Pro + OpenAI 1.93.0 API migration
- Fallback logic between models
- GUI startup error handling
- Terminal-safe logging

### Changed

- Refactored API calls into async fallback system
- Simplified `main.py` runner
- Upgraded directory structure (modular layout)

### Fixed

- Broken Gemini 404 issue
- OpenAI migration warnings
- File path loading on Windows
