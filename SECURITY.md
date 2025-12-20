# Security Policy

## Supported Versions

We actively maintain security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| latest  | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security issue, please report it responsibly.

### How to Report

1. **DO NOT** create a public GitHub issue for security vulnerabilities
2. Email us at: **security@tryonlabs.ai** (or contact maintainers directly)
3. Alternatively, use [GitHub's private vulnerability reporting](https://github.com/tryonlabs/opentryon/security/advisories/new)

### What to Include

Please provide as much information as possible:

- Type of vulnerability (e.g., credential exposure, injection, etc.)
- Location of the affected code (file path and line numbers)
- Step-by-step instructions to reproduce the issue
- Proof of concept or exploit code (if available)
- Potential impact of the vulnerability
- Suggested fix (if you have one)

### Response Timeline

- **Acknowledgment**: Within 48 hours
- **Initial Assessment**: Within 7 days
- **Resolution Target**: Within 30 days (depending on severity)

## Security Best Practices

### API Key Management

This project integrates with multiple AI service providers. When using OpenTryOn:

1. **Never commit API keys** to version control
2. **Use environment variables** or `.env` files (add `.env` to `.gitignore`)
3. **Rotate credentials** if you suspect they've been exposed
4. **Use minimal permissions** when creating API keys

### Required Environment Variables

Store these securely and never expose them:

```
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
KLING_AI_API_KEY
KLING_AI_SECRET_KEY
SEGMIND_API_KEY
GEMINI_API_KEY
BFL_API_KEY
LUMA_AI_API_KEY
OPENAI_API_KEY
ANTHROPIC_API_KEY
GOOGLE_API_KEY
```

### Secure Configuration

```bash
# Create .env file with restricted permissions
touch .env
chmod 600 .env

# Verify .env is in .gitignore
grep -q "^\.env$" .gitignore || echo ".env" >> .gitignore
```

## Known Security Considerations

### Image Processing

- Uploaded images are processed through third-party AI APIs
- Do not process images containing sensitive or private information without consent
- Be aware of the data retention policies of each API provider

### API Rate Limiting

- Implement rate limiting in production deployments
- Monitor API usage to detect potential abuse

### Dependencies

We regularly update dependencies to patch known vulnerabilities. Run:

```bash
pip install --upgrade -r requirements.txt
```

## Acknowledgments

We appreciate security researchers who help keep OpenTryOn safe. Contributors who responsibly disclose vulnerabilities will be acknowledged here (with their permission).

## Contact

- **Security Issues**: contact@tryonlabs.ai
- **General Questions**: [Discord Community](https://discord.gg/T5mPpZHxkY)
- **Bug Reports**: [GitHub Issues](https://github.com/tryonlabs/opentryon/issues)
