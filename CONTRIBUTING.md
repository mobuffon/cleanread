# Contributing to CleanRead

Thank you for considering contributing to CleanRead! This document provides guidelines for contributing to the project.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/yourusername/cleanread.git`
3. Create a branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Test your changes
6. Commit and push
7. Create a Pull Request

## Development Setup

See [SETUP.md](SETUP.md) for detailed setup instructions.

## Code Style

### Python (Backend)

- Follow PEP 8
- Use type hints
- Maximum line length: 100 characters
- Use Black for formatting: `black .`
- Use Ruff for linting: `ruff check .`

Example:
```python
from typing import Optional

def convert_pdf(file_id: str, max_pages: Optional[int] = None) -> dict:
    """Convert PDF to EPUB."""
    pass
```

### TypeScript (Frontend)

- Use ESLint configuration
- Prefer functional components
- Use TypeScript strict mode
- Maximum line length: 100 characters

Example:
```typescript
interface ConversionJob {
  jobId: string
  status: 'pending' | 'processing' | 'completed' | 'error'
}

export function convertPDF(fileId: string): Promise<ConversionJob> {
  // ...
}
```

## Commit Messages

Follow the Conventional Commits specification:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting)
- `refactor:` Code refactoring
- `test:` Test changes
- `chore:` Build/config changes

Examples:
```
feat: add email integration for send to kindle
fix: handle empty PDF files correctly
docs: update API documentation
```

## Testing

### Backend Tests

```bash
cd backend
pytest
pytest --cov  # with coverage
```

### Frontend Tests

```bash
cd frontend
npm test
npm run test:coverage
```

## Pull Request Process

1. **Update Documentation**: Update README, SETUP, or API docs if needed
2. **Add Tests**: Include tests for new features
3. **Run Linters**: Ensure code passes linting
4. **Write Clear Description**: Explain what and why
5. **Link Issues**: Reference related issues

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] New tests added
- [ ] Manual testing completed

## Screenshots (if applicable)

## Related Issues
Closes #123
```

## Feature Requests

Have an idea? Create an issue with:
- Clear description
- Use cases
- Expected behavior
- Mock-ups (if UI related)

## Bug Reports

Found a bug? Create an issue with:
- Description
- Steps to reproduce
- Expected behavior
- Actual behavior
- Environment (OS, browser, versions)
- Screenshots/logs

## Code Review Process

1. Automated checks must pass
2. At least one maintainer review
3. All comments addressed
4. Tests pass
5. Documentation updated

## Project Structure

```
clean_read/
├── backend/          # FastAPI backend
│   ├── app/
│   │   ├── api/      # API endpoints
│   │   ├── core/     # Config, security
│   │   ├── models/   # Database models
│   │   ├── services/ # Business logic
│   │   └── tasks/    # Celery tasks
│   └── tests/
├── frontend/         # React frontend
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── services/
│   └── tests/
└── docs/            # Documentation
```

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Questions?

Feel free to open an issue or reach out to maintainers.

Thank you for contributing! 🎉
