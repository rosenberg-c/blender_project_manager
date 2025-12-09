# Contributing to Blender Project Manager

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help maintain a welcoming environment for all contributors

## Getting Started

### Development Setup

1. Fork the repository
2. Clone your fork:
```bash
git clone https://github.com/yourusername/blender_project_manager.git
cd blender_project_manager
```

3. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

4. Install development dependencies:
```bash
pip install -r requirements.txt
pip install pytest pytest-qt pytest-cov
```

5. Create a feature branch:
```bash
git checkout -b feature/your-feature-name
```

## Development Guidelines

### Code Style

This project follows PEP 8 with modifications documented in `agent_instructions.md`. Key points:

- **Self-documenting code**: Clear variable and function names over comments
- **Docstrings required**: For all public methods and classes
- **Comments for organization**: Use comments to separate logical sections
- **Type hints preferred**: Use Python type hints where helpful
- **No unnecessary comments**: Code should explain what it does; comments explain why

### Project Structure

Follow the existing architecture:
- `blender_lib/`: Blender Python scripts (no GUI dependencies)
- `core/`: Core business logic
- `services/`: Service layer for external interactions
- `controllers/`: Application state management
- `gui/`: PySide6 GUI components
- `tests/`: Test suite

### Testing

Write tests for new features:
```bash
pytest tests/
```

For GUI components:
```bash
pytest tests/gui/ -v
```

Test coverage:
```bash
pytest --cov=. --cov-report=html
```

### Commit Guidelines

- Use clear, descriptive commit messages
- Reference issues when applicable: `Fix #123: Description`
- Keep commits focused on a single change
- Follow conventional commits format when possible:
  - `feat:` New features
  - `fix:` Bug fixes
  - `docs:` Documentation changes
  - `refactor:` Code refactoring
  - `test:` Test additions/changes
  - `chore:` Maintenance tasks

### Pull Request Process

1. **Update documentation**: If you add features, update README.md
2. **Add tests**: New features should include tests
3. **Check style**: Ensure code follows project conventions
4. **Run tests**: All tests should pass
5. **Write clear description**: Explain what and why
6. **Link issues**: Reference related issues

Example PR description:
```markdown
## Summary
Brief description of changes

## Changes
- List of specific changes
- What was added/modified/removed

## Testing
How the changes were tested

Fixes #123
```

### Review Process

- Maintainers will review PRs within a few days
- Be responsive to feedback
- Make requested changes in new commits
- Once approved, maintainers will merge

## Areas for Contribution

### High Priority
- Cross-platform testing (Windows, Linux)
- Performance optimizations for large projects
- Additional file format support
- Improved error handling and recovery

### Feature Ideas
- Batch operations for multiple files
- Project templates
- Asset library integration
- Undo/redo functionality
- Diff viewer for changes

### Documentation
- Video tutorials
- Use case examples
- API documentation
- Translation to other languages

### Bug Fixes
Check the issue tracker for bugs labeled `good first issue` or `help wanted`.

## Questions?

- Open an issue for bug reports or feature requests
- Start a discussion for questions or ideas
- Check existing issues before creating new ones

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
