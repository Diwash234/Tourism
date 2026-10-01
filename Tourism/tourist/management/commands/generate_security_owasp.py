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

- [ ] 1.1.1: Secure development lifecycle
- [ ] 1.2.1: Authentication architecture
- [ ] 1.3.1: Session management architecture
- [ ] 1.4.1: Access control architecture
- [ ] 1.5.1: Input validation architecture
- [ ] 1.6.1: Output encoding architecture
- [ ] 1.7.1: Cryptographic architecture
- [ ] 1.8.1: Error handling architecture
- [ ] 1.9.1: Data protection architecture
- [ ] 1.10.1: Communications architecture
- [ ] 1.11.1: Malicious software architecture
- [ ] 1.12.1: Business logic architecture
- [ ] 1.13.1: Secure file upload architecture
- [ ] 1.14.1: API architecture

## V2: Authentication

- [ ] 2.1.1: Password security
- [ ] 2.2.1: General authenticator security
- [ ] 2.3.1: Authenticator lifecycle
- [ ] 2.4.1: Credential storage
- [ ] 2.5.1: Credential recovery
- [ ] 2.6.1: Look-up secret verifier
- [ ] 2.7.1: Out of band verifier
- [ ] 2.8.1: Single or multi factor one time verifier
- [ ] 2.9.1: Cryptographic software and devices
- [ ] 2.10.1: Service authentication

## V3: Session Management

- [ ] 3.1.1: Session management control
- [ ] 3.2.1: Session binding
- [ ] 3.3.1: Session termination
- [ ] 3.4.1: Cookie-based session management
- [ ] 3.5.1: Defenses against session management exploits
- [ ] 3.6.1: Defenses against cross site request forgery
- [ ] 3.7.1: Defenses against cross site script inclusion

## V4: Access Control

- [ ] 4.1.1: General access control design
- [ ] 4.2.1: Operation level access control
- [ ] 4.3.1: Other access control considerations

## V5: Validation

- [ ] 5.1.1: Input validation
- [ ] 5.2.1: Sanitization and sandboxing
- [ ] 5.3.1: Output encoding and injection prevention
- [ ] 5.4.1: Memory, string, and unmanaged code
- [ ] 5.5.1: Deserialization prevention

## V6: Cryptography

- [ ] 6.1.1: Data classification
- [ ] 6.2.1: Algorithms
- [ ] 6.3.1: Random values
- [ ] 6.4.1: Secret management

## V7: Error Handling

- [ ] 7.1.1: Log content
- [ ] 7.2.1: Log processing
- [ ] 7.3.1: Error handling

## V8: Data Protection

- [ ] 8.1.1: General data protection
- [ ] 8.2.1: Client-side data protection
- [ ] 8.3.1: Sensitive private data

## V9: Communications

- [ ] 9.1.1: Server communication security
- [ ] 9.2.1: Client communication security

## V10: Malicious Software

- [ ] 10.1.1: Code integrity controls
- [ ] 10.2.1: Malicious code search
- [ ] 10.3.1: Deployed application integrity controls

## V11: Business Logic

- [ ] 11.1.1: Business logic security
- [ ] 11.2.1: Anti-automation controls

## V12: Files and Resources

- [ ] 12.1.1: File upload restrictions
- [ ] 12.2.1: File integrity verification
- [ ] 12.3.1: File execution
- [ ] 12.4.1: File storage
- [ ] 12.5.1: File download
- [ ] 12.6.1: SSRF protection

## V13: API and Web Service

- [ ] 13.1.1: General API and web service security
- [ ] 13.2.1: RESTful web service
- [ ] 13.3.1: SOAP web service
- [ ] 13.4.1: GraphQL

## V14: Configuration

- [ ] 14.1.1: Build and deploy
- [ ] 14.2.1: Dependency
- [ ] 14.3.1: Unintended security disclosure
- [ ] 14.4.1: HTTP header security
- [ ] 14.5.1: HTTP request header validation
"""

        with open(docs_dir / "OWASP_ASVS.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"OWASP ASVS checklist generated at {docs_dir / 'OWASP_ASVS.md'}"))
