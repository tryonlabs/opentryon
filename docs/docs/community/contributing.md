# Contributing

We welcome contributions to OpenTryOn! This guide will help you get started.

## How to Contribute

### 1. Open an Issue

Before making changes, we recommend:
- Opening an issue to discuss your intended changes
- Checking if an issue already exists
- Discussing the approach with maintainers

### 2. Fork and Clone

```bash
# Fork the repository on GitHub
git clone https://github.com/YOUR_USERNAME/opentryon.git
cd opentryon
```

### 3. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

### 4. Make Changes

- Write clean, documented code
- Follow PEP 8 style guidelines
- Add tests for new features
- Update documentation

### 5. Test Your Changes

```bash
# Run tests
pytest tests/

# Check code style
flake8 .
```

### 6. Submit a Pull Request

- Push to your fork
- Create a pull request to the main branch
- Describe your changes clearly
- Reference any related issues

## Development Setup

```bash
# Clone repository
git clone https://github.com/tryonlabs/opentryon.git
cd opentryon

# Create development environment
conda env create -f environment.yml
conda activate opentryon

# Install in development mode
pip install -e ".[dev]"
```

## Code Style

- Follow PEP 8
- Use type hints where possible
- Document functions with docstrings
- Keep functions focused and modular

## Areas for Contribution

- New features
- Bug fixes
- Documentation improvements
- Performance optimizations
- Test coverage
- Examples and tutorials

## Questions?

- Join our [Discord](https://discord.gg/T5mPpZHxkY)
- Open an issue on [GitHub](https://github.com/tryonlabs/opentryon/issues)

Thank you for contributing! 🎉

