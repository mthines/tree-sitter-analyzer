# Security Policy

## Supported Versions

The following versions of CodeXray are currently being supported with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 1.9.x   | :white_check_mark: |
| 1.8.x   | :white_check_mark: |
| < 1.8.0 | :x:                |

## Reporting a Vulnerability

We take the security of CodeXray seriously. If you discover a security vulnerability, please follow these steps:

### How to Report

1. **Do NOT create a public GitHub issue** for security vulnerabilities.

2. **Email us directly** at: aimasteracc@gmail.com
   - Use the subject line: `[SECURITY] codexray vulnerability report`
   - Include as much detail as possible about the vulnerability

3. **Alternatively**, use [GitHub's private vulnerability reporting](https://github.com/aimasteracc/tree-sitter-analyzer/security/advisories/new) to submit your report.

### What to Include

Please include the following information in your report:

- Description of the vulnerability
- Steps to reproduce the issue
- Potential impact of the vulnerability
- Any suggested fixes (if available)
- Your contact information for follow-up

### Response Timeline

- **Initial Response**: Within 48 hours of receiving your report
- **Status Update**: Within 7 days with our assessment
- **Resolution Target**: Critical vulnerabilities within 30 days, others within 90 days

### What to Expect

1. We will acknowledge receipt of your vulnerability report
2. We will investigate and validate the reported issue
3. We will work on a fix and coordinate the disclosure timeline with you
4. We will publicly acknowledge your contribution (unless you prefer to remain anonymous)

### Safe Harbor

We consider security research conducted in accordance with this policy to be:

- Authorized concerning any applicable anti-hacking laws
- Authorized concerning any relevant anti-circumvention laws
- Exempt from restrictions in our Terms of Service that would interfere with security research

We will not pursue civil action or initiate a complaint to law enforcement for accidental, good-faith violations of this policy.

## Security Best Practices

When using CodeXray:

1. **Keep Updated**: Always use the latest stable version
2. **Environment Variables**: Use `TREE_SITTER_PROJECT_ROOT` to restrict file access
3. **Path Validation**: The tool validates file paths to prevent directory traversal attacks
4. **Input Sanitization**: All file inputs are sanitized before processing

## Security Features

CodeXray includes built-in security measures:

- **Path Traversal Protection**: Prevents access outside allowed directories
- **File Size Limits**: Prevents denial of service from extremely large files
- **Input Validation**: All inputs are validated before processing
- **Secure Defaults**: Conservative default settings for security-sensitive options

## Contact

For general security inquiries, please contact: aimasteracc@gmail.com

---

Thank you for helping keep CodeXray and its users safe!
