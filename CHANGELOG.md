# Changelog

## [5.1.1] – 2025-07-03
### Added
- Full OpenAI v1.x SDK migration (`OpenAI()` client)  
- Gemini upgraded to use `gemini-2.5-pro` model  
- Automatic environment cleanup instructions  
### Fixed
- Eliminated legacy `openai.ChatCompletion.create` calls  
- Resolved 404 errors from invalid Gemini model name  
- Cleared up cached `.pyc` conflicts and Anaconda vs venv confusion
