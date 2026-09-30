"""
Management command to generate OWASP ASVS checklist.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate OWASP ASVS checklist"

    def handle(self, *args, **options):
        self.stdout.write("Generating OWASP ASVS checklist...")

        docs_dir = Path("docs/security")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# OWASP ASVS Checklist

## V1: Architecture

- [ ] Secure development lifecycle
- [ ] Threat modeling
- [ ] Security requirements

## V2: Authentication

- [ ] Password security
- [ ] Multi-factor authentication
- [ ] Session management
- [ ] Registration and verification

## V3: Session Management

- [ ] Session generation
- [ ] Session binding
- [ ] Session termination
- [ ] Session fixation prevention

## V4: Access Control

- [ ] Principle of least privilege
- [ ] Server-side authorization
- [ ] Attribute-based access control

## V5: Validation

- [ ] Input validation
- [ ] Output encoding
- [ ] Parameterized queries
- [ ] File upload validation

## V6: Cryptography

- [ ] Data classification
- [ ] Encryption at rest
- [ ] Encryption in transit
- [ ] Key management

## V7: Error Handling

- [ ] Error handling strategy
- [ ] Logging
- [ ] No sensitive data in errors

## V8: Data Protection

- [ ] Data minimization
- [ ] Data retention
- [ ] Data deletion

## V9: Communications

- [ ] TLS configuration
- [ ] Certificate validation
- [ ] Secure headers

## V10: Malicious Input

- [ ] Anti-CSRF
- [ ] Anti-XSS
- [ ] Anti-SQL injection
- [ ] Anti-command injection

## V11: Business Logic

- [ ] Business logic validation
- [ ] Rate limiting
- [ ] Workflow validation

## V12: File and Resources

- [ ] File upload restrictions
- [ ] File download restrictions
- [ ] Path traversal prevention

## V13: API and Web Service

- [ ] API authentication
- [ ] API authorization
- [ ] API rate limiting
- [ ] API input validation

## V14: Configuration

- [ ] Secure configuration
- [ ] Dependency management
- [ ] Security headers
- [ ] Error pages
"""

        with open(docs_dir / "OWASP_ASVS.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"OWASP ASVS checklist generated at {docs_dir / 'OWASP_ASVS.md'}"))
