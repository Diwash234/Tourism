"""
Management command to generate HIPAA Security Rule checklist.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate HIPAA Security Rule checklist"

    def handle(self, *args, **options):
        self.stdout.write("Generating HIPAA Security Rule checklist...")

        docs_dir = Path("docs/security")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# HIPAA Security Rule Checklist

## Administrative Safeguards (164.308)

### Security Management Process
- [ ] 164.308(a)(1)(i): Security Management Process
- [ ] 164.308(a)(1)(ii)(A): Risk Analysis
- [ ] 164.308(a)(1)(ii)(B): Risk Management
- [ ] 164.308(a)(1)(ii)(C): Sanction Policy
- [ ] 164.308(a)(1)(ii)(D): Information System Activity Review

### Assigned Security Responsibility
- [ ] 164.308(a)(2): Security Official

### Workforce Security
- [ ] 164.308(a)(3)(i): Authorization and/or Supervision
- [ ] 164.308(a)(3)(ii)(A): Workforce Clearance Procedure
- [ ] 164.308(a)(3)(ii)(B): Termination Procedures

### Information Access Management
- [ ] 164.308(a)(4)(i): Access Authorization
- [ ] 164.308(a)(4)(ii)(A): Access Establishment and Modification
- [ ] 164.308(a)(4)(ii)(B): Access Granting
- [ ] 164.308(a)(4)(ii)(C): Access Termination

### Security Awareness and Training
- [ ] 164.308(a)(5)(i): Security Reminders
- [ ] 164.308(a)(5)(ii)(A): Protection from Malicious Software
- [ ] 164.308(a)(5)(ii)(B): Login Monitoring
- [ ] 164.308(a)(5)(ii)(C): Password Management

### Security Incident Procedures
- [ ] 164.308(a)(6)(i): Response and Reporting
- [ ] 164.308(a)(6)(ii): Response and Reporting

### Contingency Plan
- [ ] 164.308(a)(7)(i): Data Backup Plan
- [ ] 164.308(a)(7)(ii)(A): Disaster Recovery Plan
- [ ] 164.308(a)(7)(ii)(B): Emergency Mode Operation Plan
- [ ] 164.308(a)(7)(ii)(C): Testing and Revision Procedure
- [ ] 164.308(a)(7)(ii)(D): Applications and Data Criticality Analysis

### Evaluation
- [ ] 164.308(a)(8): Evaluation

### Business Associate Contracts
- [ ] 164.308(b)(1): Business Associate Contracts
- [ ] 164.308(b)(2): Business Associate Contracts
- [ ] 164.308(b)(3): Business Associate Contracts
- [ ] 164.308(b)(4): Business Associate Contracts

## Physical Safeguards (164.310)

### Facility Access Controls
- [ ] 164.310(a)(1): Contingency Operations
- [ ] 164.310(a)(2)(i): Facility Security Plan
- [ ] 164.310(a)(2)(ii): Access Control and Validation Procedures
- [ ] 164.310(a)(2)(iii): Maintenance Records

### Workstation Use
- [ ] 164.310(b): Workstation Use

### Workstation Security
- [ ] 164.310(c): Workstation Security

### Device and Media Controls
- [ ] 164.310(d)(1): Disposal
- [ ] 164.310(d)(2)(i): Media Re-use
- [ ] 164.310(d)(2)(ii): Accountability
- [ ] 164.310(d)(2)(iii): Data Backup and Storage

## Technical Safeguards (164.312)

### Access Control
- [ ] 164.312(a)(1): Access Control
- [ ] 164.312(a)(2)(i): Unique User Identification
- [ ] 164.312(a)(2)(ii): Emergency Access Procedure
- [ ] 164.312(a)(2)(iii): Automatic Logoff
- [ ] 164.312(a)(2)(iv): Encryption and Decryption

### Audit Controls
- [ ] 164.312(b): Audit Controls

### Integrity
- [ ] 164.312(c)(1): Mechanism to Authenticate ePHI
- [ ] 164.312(c)(2): Mechanism to Authenticate ePHI

### Person or Entity Authentication
- [ ] 164.312(d): Person or Entity Authentication

### Transmission Security
- [ ] 164.312(e)(1): Transmission Security
- [ ] 164.312(e)(2)(i): Integrity Controls
- [ ] 164.312(e)(2)(ii): Encryption

## Organizational Requirements (164.314)

### Business Associate Contracts
- [ ] 164.314(a)(1): Business Associate Contracts
- [ ] 164.314(a)(2)(i): Business Associate Contracts
- [ ] 164.314(a)(2)(ii): Business Associate Contracts
- [ ] 164.314(b)(1): Business Associate Contracts

### Requirements for Group Health Plans
- [ ] 164.314(b)(2): Requirements for Group Health Plans

## Policies and Procedures (164.316)

### Policies and Procedures
- [ ] 164.316(a): Policies and Procedures

### Documentation
- [ ] 164.316(b)(1): Documentation
- [ ] 164.316(b)(2)(i): Time Limit
- [ ] 164.316(b)(2)(ii): Availability
- [ ] 164.316(b)(2)(iii): Updates
"""

        with open(docs_dir / "HIPAA_SECURITY.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"HIPAA Security Rule checklist generated at {docs_dir / 'HIPAA_SECURITY.md'}"))
