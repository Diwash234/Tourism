"""
Management command to generate a .gitignore file.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate a .gitignore file"

    def handle(self, *args, **options):
        self.stdout.write("Generating .gitignore...")

        content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
*.egg-info/
dist/
build/

# Django
*.log
*.pot
*.pyc
db.sqlite3
db.sqlite3-journal
media/
staticfiles/

# Environment
.env
.venv/
venv/
env/

# Node
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
dist/
.vite/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Docker
.dockerignore

# Testing
.coverage
htmlcov/
.pytest_cache/

# Misc
*.bak
*.tmp
"""

        with open(Path(".gitignore"), "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(".gitignore generated"))
