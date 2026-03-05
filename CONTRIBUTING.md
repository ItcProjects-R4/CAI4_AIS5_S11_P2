# Contributing to Customer Data ETL

Thank you for your interest in contributing! Please follow these guidelines to ensure a smooth collaboration.

## Code Style

- **Python:** Follow PEP 8. Use Black (100 char lines) and isort for formatting.
- **Pre-commit:** Install hooks with `pre-commit install` to automatically check code before commit.
- **Linting:** Run `make lint` to check for issues.

## Branching

- `main` is the production-ready branch. Always keep it clean and working.
- Create feature branches: `feature/your-feature-name` or `fix/your-fix-name`
- Branch from `main` and push feature branches to origin.

## Pull Requests

1. Ensure all tests pass: `make test`
2. Ensure linting passes: `make lint`
3. Add or update tests for new functionality
4. Update documentation (README.md, docstrings) if needed
5. Write clear commit messages: "Fix: ...", "Feature: ...", "Docs: ..."
6. Request review from at least one project maintainer

## Testing

- Write unit tests in `tests/` using pytest
- Run tests inside Docker: `make test`
- Aim for >80% code coverage for new modules
- Use `monkeypatch` and temporary directories (`tmpdir`) in fixtures for isolation

## Documentation

- Include docstrings for all modules, classes, and functions
- Use reStructuredText (reST) format for docstrings
- Keep README.md and other docs up to date
- Include examples and usage instructions for new features

## Reporting Issues

- Check existing issues before creating a new one
- Include reproduction steps, expected behavior, and actual behavior
- Include environment details: OS, Python version, Docker version

## Local Development Workflow

```bash
# 1. Clone and set up
git clone <repo>
cd customer-data-etl
docker compose build

# 2. Install pre-commit hooks
make install-hooks

# 3. Create feature branch
git checkout -b feature/my-feature

# 4. Make changes and test
make shell      # Drop into container
pytest          # Run tests
flake8 src tests # Check style
black src tests # Format

# 5. Commit and push
git add .
git commit -m "Feature: add new data source handler"
git push origin feature/my-feature

# 6. Create Pull Request on GitHub
# Include description, related issues, and testing notes
```

## Questions?

- Check the README.md for setup and usage
- Review existing code for patterns and conventions
- Ask in GitHub Issues if something is unclear

Thanks for contributing!
