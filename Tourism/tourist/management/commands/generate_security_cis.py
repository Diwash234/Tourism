"""
Management command to generate CIS benchmark checklist.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate CIS benchmark checklist"

    def handle(self, *args, **options):
        self.stdout.write("Generating CIS benchmark checklist...")

        docs_dir = Path("docs/security")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# CIS Benchmark Checklist

## Level 1 - Essential

### 1. Inventory and Control of Hardware Assets
- [ ] Maintain hardware inventory
- [ ] Track hardware assets

### 2. Inventory and Control of Software Assets
- [ ] Maintain software inventory
- [ ] Track software assets

### 3. Continuous Vulnerability Management
- [ ] Run vulnerability scans
- [ ] Remediate vulnerabilities

### 4. Controlled Use of Administrative Privileges
- [ ] Use separate admin accounts
- [ ] Limit admin access

### 5. Secure Configuration for Hardware and Software
- [ ] Establish secure configurations
- [ ] Implement configuration management

### 6. Maintenance, Monitoring, and Analysis of Audit Logs
- [ ] Collect audit logs
- [ ] Review audit logs

### 7. Email and Web Browser Protections
- [ ] Configure email protections
- [ ] Configure web protections

### 8. Malware Defenses
- [ ] Deploy anti-malware
- [ ] Configure anti-malware

### 9. Limitation and Control of Network Ports
- [ ] Close unused ports
- [ ] Restrict port access

### 10. Data Recovery Capabilities
- [ ] Implement backups
- [ ] Test backups

### 11. Secure Configuration for Network Devices
- [ ] Secure firewall config
- [ ] Secure router config

### 12. Boundary Defense
- [ ] Deploy firewalls
- [ ] Implement IDS/IPS

### 13. Data Protection
- [ ] Classify data
- [ ] Protect sensitive data

### 14. Controlled Access Based on Need to Know
- [ ] Implement access controls
- [ ] Review access regularly

### 15. Wireless Access Control
- [ ] Secure wireless networks
- [ ] Monitor wireless access

### 16. Account Monitoring and Control
- [ ] Monitor accounts
- [ ] Disable unused accounts

## Level 2 - Enhanced

### 17. Implement a Security Awareness Program
- [ ] Conduct security training
- [ ] Test awareness

### 18. Application Software Security
- [ ] Secure development practices
- [ ] Code reviews

### 19. Incident Response and Management
- [ ] Incident response plan
- [ ] Incident response testing

### 20. Penetration Tests and Red Team Exercises
- [ ] Conduct penetration tests
- [ ] Remediate findings
"""

        with open(docs_dir / "CIS_BENCHMARK.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"CIS benchmark checklist generated at {docs_dir / 'CIS_BENCHMARK.md'}"))
