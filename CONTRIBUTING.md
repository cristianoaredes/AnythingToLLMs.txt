# Contributing to Anything to LLMs.txt

Thank you for considering contributing to Anything to LLMs.txt! This document provides guidelines and instructions to help you get started.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for everyone.

## How Can I Contribute?

### Reporting Bugs

- Check if the bug has already been reported in [Issues](https://github.com/cristianocosta/anything-to-llms-txt/issues)
- Use the bug report template when creating a new issue
- Include detailed steps to reproduce the bug
- Include system information (OS, Python version, etc.)
- If possible, include a minimal code example that reproduces the issue

### Suggesting Features

- Check if the feature has already been suggested in [Issues](https://github.com/cristianocosta/anything-to-llms-txt/issues)
- Use the feature request template when creating a new issue
- Clearly describe the feature and its benefits
- Provide examples of how the feature would be used

### Pull Requests

1. Fork the repository
2. Create a new branch (`git checkout -b feature/your-feature-name`)
3. Make your changes
4. Run tests to ensure nothing breaks (`pytest`)
5. Update documentation if necessary
6. Commit your changes with descriptive commit messages
7. Push to your branch (`git push origin feature/your-feature-name`)
8. Create a Pull Request against the `main` branch

## Development Environment

1. Clone your fork of the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -e .  # Install in development mode
   ```
3. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt  # If available
   ```

## Code Style

- Follow PEP 8 guidelines
- Use meaningful variable and function names
- Include docstrings for all functions, classes, and modules
- Keep code complexity to a minimum

## Testing

- Add tests for new features or bug fixes
- Ensure all tests pass before submitting a PR
- Run the test suite:
  ```bash
  pytest
  ```

## Documentation

- Update documentation for any changed functionality
- Include examples for new features
- Make sure code comments are clear and useful

## Commit Messages

- Use clear, descriptive commit messages
- Start with a short summary (50 chars or less)
- Reference issues if applicable (`Fix #123`, `Closes #456`)

## Review Process

- All PRs will be reviewed by at least one maintainer
- Address any requested changes promptly
- Be open to feedback and suggestions

Thank you for your contributions!
