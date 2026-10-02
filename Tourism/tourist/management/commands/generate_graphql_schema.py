"""
Management command to generate GraphQL schema.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate GraphQL schema"

    def handle(self, *args, **options):
        self.stdout.write("Generating GraphQL schema...")

        docs_dir = Path("docs/graphql")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# GraphQL Schema

## Queries

### Get all destinations
```graphql
query {
  allDestinations {
    id
    name
    slug
    description
    district
    province
  }
}
```

### Get a single destination
```graphql
query {
  destination(slug: "pokhara") {
    id
    name
    slug
    description
    district
    province
  }
}
```
"""

        with open(docs_dir / "SCHEMA.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"GraphQL schema generated at {docs_dir / 'SCHEMA.md'}"))
