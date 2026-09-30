"""
Management command to generate a security glossary.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate a security glossary"

    def handle(self, *args, **options):
        self.stdout.write("Generating security glossary...")

        docs_dir = Path("docs/security")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# Security Glossary

## A
- **Authentication** - Verifying identity
- **Authorization** - Granting permissions
- **Availability** - Ensuring service uptime

## C
- **CVE** - Common Vulnerabilities and Exposures
- **CSRF** - Cross-Site Request Forgery

## D
- **DDoS** - Distributed Denial of Service

## E
- **Encryption** - Converting data to unreadable format

## I
- **IDOR** - Insecure Direct Object Reference

## M
- **MFA** - Multi-Factor Authentication

## P
- **PII** - Personally Identifiable Information

## S
- **SQL Injection** - Code injection technique
- **SSO** - Single Sign-On

## V
- **Vulnerability** - Security weakness

## X
- **XSS** - Cross-Site Scripting
"""

        with open(docs_dir / "GLOSSARY.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Security glossary generated at {docs_dir / 'GLOSSARY.md'}"))
