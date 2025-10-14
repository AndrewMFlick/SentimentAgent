# Contributing to Reddit Sentiment Analysis

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Development Setup

1. Follow the setup instructions in [QUICKSTART.md](QUICKSTART.md)
2. Run the setup script: `./setup.sh`
3. Ensure tests pass: `cd backend && pytest`

## Code Style

### Python (Backend)
- Follow PEP 8 style guide
- Use type hints for function parameters and returns
- Document functions with docstrings
- Run linting before committing

### TypeScript (Frontend)
- Follow the existing code style
- Use functional components with hooks
- Add prop types for components
- Run `npm run lint` before committing

## Testing

### Backend Tests
```bash
cd backend
pytest
pytest --cov=src  # With coverage
```

### Adding New Tests
- Place tests in `backend/tests/`
- Name test files as `test_*.py`
- Use descriptive test names

## Pull Request Process

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Update documentation if needed
7. Commit with clear messages
8. Push to your fork
9. Open a Pull Request

## Commit Messages

Use clear, descriptive commit messages:
- `feat: Add new feature`
- `fix: Fix bug in sentiment analysis`
- `docs: Update README`
- `test: Add tests for trending analyzer`
- `refactor: Improve database query performance`

## Feature Requests

Open an issue with:
- Clear description of the feature
- Use case / motivation
- Proposed implementation (optional)

## Bug Reports

Include:
- Clear description of the bug
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, etc.)
- Relevant logs or error messages

## Questions?

Open an issue with the `question` label.
