# Test TODOs for >90% Coverage

This file lists all the test scenarios needed to achieve high coverage and robust quality for the project.

---

## 1. DocumentConverterTool (src/tools/document_converter.py)
- [ ] Convert supported file types (PDF, DOCX, HTML, TXT, etc.)
- [ ] Handle unsupported file types (should raise warning or error)
- [ ] Conversion with/without OCR
- [ ] Conversion with different chunk sizes and overlaps
- [ ] Conversion with/without plugins
- [ ] File not found error
- [ ] Docling import failure
- [ ] Docling pipeline misconfiguration
- [ ] Conversion failure (simulate Docling exceptions)
- [ ] Output file creation and content validation
- [ ] Output directory creation
- [ ] Output in multiple formats (llms, md, json, html)
- [ ] Batch processing: multiple files in a directory
- [ ] Batch processing: empty directory
- [ ] Batch processing: partially corrupt files
- [ ] Export to LangChain (stub)
- [ ] Extract tables, images, and raw text

## 2. LLMSFormatter (src/tools/llms_formatter.py)
- [ ] Format all output profiles: llms-min, llms-ctx, llms-tables, llms-images, llms-raw, llms-full
- [ ] Metadata inclusion (title, date, source, author, etc.)
- [ ] Summary extraction (explicit and automatic)
- [ ] Table and image formatting
- [ ] Raw section formatting
- [ ] Token analysis section
- [ ] Empty document
- [ ] Document with only tables/images
- [ ] Document with missing metadata
- [ ] Document with very large content (test truncation/limits)
- [ ] Exception in summary extraction
- [ ] Exception in content formatting

## 3. TokenAnalyzer & count_tokens (src/tools/token_analyzer.py, token_counter.py)
- [ ] Count tokens for different models (gpt-3.5, gpt-4, etc.)
- [ ] Handle unknown model names
- [ ] Handle empty or malformed input
- [ ] Model limit warnings
- [ ] Usage percentage calculation
- [ ] Recommendations for chunking/model

## 4. SmolDoclingProcessor (src/tools/smoldocling_processor.py)
- [ ] Process supported file types
- [ ] Handle unsupported file types
- [ ] Simulate Docling errors
- [ ] Handle missing dependencies

## 5. API (src/api/)
- [ ] /v1/analyzer/tokens: valid/invalid payloads, missing fields
- [ ] /v1/analyzer/detect-content-type: valid/invalid payloads
- [ ] /v1/convert/: valid file upload, unsupported file, missing file
- [ ] /v1/convert/{job_id}: job status polling, completed/failed jobs
- [ ] Internal server errors
- [ ] Invalid JSON
- [ ] File upload errors
- [ ] Job queueing and status updates (simulate Redis)
- [ ] Worker processing simulation

## 6. CLI (src/main.py)
- [ ] All CLI options and flags
- [ ] Invalid/missing arguments
- [ ] End-to-end conversion from CLI
- [ ] Output file creation
- [ ] Error messages for invalid input

## 7. Utils (src/utils/logging_config.py)
- [ ] Logger creation and configuration
- [ ] Logging at different levels

## 8. Edge/Negative Cases
- [ ] Permission errors (output directory unwritable)
- [ ] Disk full or IO errors
- [ ] Corrupt or partially written files
- [ ] Large file handling (simulate with mocks)

## 9. Test Doubles/Mocks
- [ ] Mock Docling for deterministic tests
- [ ] Mock file system operations (using tmp_path or mock)
- [ ] Mock Redis/queue for API/worker tests

## 10. Planned/Stubbed Features
- [ ] Stubs for PluginManager, ExportManager, CacheManager, DocumentValidator, OCRManager (ensure at least stub code is covered)
- [ ] Web UI endpoints (if any stubs exist)

## 11. General
- [ ] All public methods and classes should have at least one test
- [ ] All error/exception branches should be exercised
- [ ] All configuration options should be tested

---

*Update this file as you add or complete tests. Use pytest-cov to track coverage progress.*
