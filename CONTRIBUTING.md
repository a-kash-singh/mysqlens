# Contributing to MySQLens

Thank you for your interest in contributing to MySQLens! This document provides guidelines and instructions for contributing.

## 🤝 How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- MySQL version and environment details
- Relevant logs or error messages

### Suggesting Features

We welcome feature suggestions! Please create an issue with:
- Clear description of the feature
- Use case and benefits
- Potential implementation approach (optional)

### Pull Requests

1. **Fork the repository**
2. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**:
   - Follow existing code style
   - Add tests for new features
   - Update documentation as needed

4. **Test your changes**:
   ```bash
   # Backend tests
   cd backend
   pytest
   
   # Frontend build
   cd frontend
   npm run build
   ```

5. **Commit your changes**:
   ```bash
   git commit -m "feat: add your feature description"
   ```
   
   Follow [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat:` - New feature
   - `fix:` - Bug fix
   - `docs:` - Documentation changes
   - `style:` - Code style changes (formatting, etc.)
   - `refactor:` - Code refactoring
   - `test:` - Adding or updating tests
   - `chore:` - Maintenance tasks

6. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create a Pull Request** on GitHub

## 🏗️ Development Setup

### Backend Development

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server
python main.py
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

### Environment Configuration

Copy `.env.example` to `.env` and configure:
- LLM provider settings
- Database connection (for testing)
- Development flags

## 📝 Code Style

### Python (Backend)
- Follow PEP 8
- Use type hints
- Add docstrings for functions and classes
- Run `black` for formatting:
  ```bash
  black backend/
  ```
- Run `flake8` for linting:
  ```bash
  flake8 backend/
  ```

### TypeScript/React (Frontend)
- Follow React best practices
- Use TypeScript strict mode
- Use functional components with hooks
- Run linter:
  ```bash
  npm run lint
  ```

## 🧪 Testing

### Backend Tests

```bash
cd backend
pytest tests/ -v
```

Write tests for:
- Service layer (metric_service, index_advisor, etc.)
- API endpoints
- Database connections
- LLM integrations

### Frontend Tests

```bash
cd frontend
npm test
```

## 📚 Documentation

- Update README.md for user-facing changes
- Update inline code documentation
- Add JSDoc/docstrings for new functions
- Update API documentation in OpenAPI spec

## 🔍 Code Review Process

All PRs will be reviewed for:
- Code quality and style
- Test coverage
- Documentation completeness
- Performance implications
- Security considerations

## 🐛 Debugging Tips

### Backend Debugging

```python
# Enable debug logging
LOG_LEVEL=DEBUG python main.py

# Use debugger
import pdb; pdb.set_trace()
```

### Frontend Debugging

```typescript
// Console logging
console.log('Debug:', data)

// React DevTools
// Install React DevTools browser extension
```

## 📦 Release Process

1. Update version in `package.json` and `main.py`
2. Update CHANGELOG.md
3. Create release PR
4. Tag release: `git tag v1.x.x`
5. Build and push Docker images

## 🙏 Thank You!

Your contributions make MySQLens better for everyone. We appreciate your time and effort!

## 📞 Contact

- Open an issue for bugs or features
- Discussions for questions and ideas
- Email: [your-email@example.com]

---

Happy coding! 🚀
