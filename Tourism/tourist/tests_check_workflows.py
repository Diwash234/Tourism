"""Tests for the workflow checker.

The failure this guards against already happened: repair-place-images.yml
called two management commands that did not exist, and every dispatch of that
workflow failed at its first step. Nothing in CI noticed, because CI never
looked at the workflow files.
"""
from __future__ import annotations

import tempfile
from io import StringIO
from pathlib import Path

from django.core.management import call_command
from django.test import SimpleTestCase


class WorkflowCheckTests(SimpleTestCase):
    def _run(self, workflows: dict[str, str]):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            directory = root / ".github" / "workflows"
            directory.mkdir(parents=True)
            for name, text in workflows.items():
                (directory / name).write_text(text, encoding="utf-8")
            out = StringIO()
            err = StringIO()
            code = None
            try:
                call_command("check_workflows", dir=str(root), stdout=out, stderr=err)
            except SystemExit as exc:
                code = exc.code
            return out.getvalue(), err.getvalue(), code

    def test_valid_workflow_passes(self):
        output, _, code = self._run({
            "ci.yml": (
                "name: CI\n"
                "on: [push]\n"
                "jobs:\n"
                "  backend:\n"
                "    runs-on: ubuntu-latest\n"
                "    timeout-minutes: 30\n"
                "    steps:\n"
                "      - run: python manage.py test\n"
            )
        })
        self.assertIsNone(code)
        self.assertIn("YAML valid", output)
        self.assertIn("all 1 workflow(s) valid", output)

    def test_malformed_yaml_is_reported(self):
        output, _, code = self._run({"broken.yml": "name: CI\njobs:\n  - [unclosed\n"})
        self.assertEqual(code, 1)
        self.assertIn("YAML INVALID", output)

    def test_duplicate_key_is_reported(self):
        """A duplicate key is silent in most YAML readers -- the second one just
        wins -- so it has to be checked explicitly."""
        output, _, code = self._run({
            "dupe.yml": (
                "name: CI\n"
                "on: [push]\n"
                "env:\n"
                "  A: '1'\n"
                "jobs:\n"
                "  backend:\n"
                "    timeout-minutes: 30\n"
                "    env:\n"
                "      A: '1'\n"
                "    env:\n"
                "      A: '2'\n"
                "    steps:\n"
                "      - run: echo hi\n"
            )
        })
        self.assertEqual(code, 1)
        self.assertIn("duplicate key", output)

    def test_missing_management_command_is_reported(self):
        """The exact bug that broke repair-place-images.yml."""
        output, _, code = self._run({
            "ci.yml": (
                "name: CI\n"
                "on: [push]\n"
                "jobs:\n"
                "  backend:\n"
                "    timeout-minutes: 30\n"
                "    steps:\n"
                "      - run: python manage.py definitely_not_a_command\n"
            )
        })
        self.assertEqual(code, 1)
        self.assertIn("MISSING", output)
        self.assertIn("definitely_not_a_command", output)

    def test_existing_management_command_is_accepted(self):
        output, _, code = self._run({
            "ci.yml": (
                "name: CI\n"
                "on: [push]\n"
                "jobs:\n"
                "  backend:\n"
                "    timeout-minutes: 30\n"
                "    steps:\n"
                "      - run: python manage.py audit_coordinates\n"
            )
        })
        self.assertIsNone(code)
        self.assertIn("audit_coordinates: found", output)

    def test_builtin_django_commands_are_not_flagged(self):
        output, _, code = self._run({
            "ci.yml": (
                "name: CI\n"
                "on: [push]\n"
                "jobs:\n"
                "  backend:\n"
                "    timeout-minutes: 30\n"
                "    steps:\n"
                "      - run: |\n"
                "          python manage.py migrate\n"
                "          python manage.py collectstatic --noinput\n"
                "          python manage.py check\n"
            )
        })
        self.assertIsNone(code)
        self.assertIn("no custom management commands referenced", output)

    def test_missing_timeout_is_flagged_per_job(self):
        """Per job, not per file: one job's timeout must not excuse another."""
        output, _, code = self._run({
            "ci.yml": (
                "name: CI\n"
                "on: [push]\n"
                "jobs:\n"
                "  backend:\n"
                "    timeout-minutes: 30\n"
                "    steps:\n"
                "      - run: echo hi\n"
                "  frontend:\n"
                "    runs-on: ubuntu-latest\n"
                "    steps:\n"
                "      - run: echo hi\n"
            )
        })
        self.assertIsNone(code)
        self.assertIn("job frontend: no timeout-minutes", output)
        self.assertNotIn("job backend: no timeout-minutes", output)

    def test_workflow_without_jobs_is_reported(self):
        output, _, code = self._run({"ci.yml": "name: CI\non: [push]\n"})
        self.assertEqual(code, 1)
        self.assertIn("no 'jobs' key", output)

    def test_empty_workflow_directory_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".github" / "workflows").mkdir(parents=True)
            out = StringIO()
            code = None
            try:
                call_command("check_workflows", dir=str(root), stdout=out, stderr=out)
            except SystemExit as exc:
                code = exc.code
            self.assertEqual(code, 1)
            self.assertIn("no workflow files", out.getvalue())


class RepositoryWorkflowsTests(SimpleTestCase):
    """The real files, not fixtures. This is the test that would have caught
    the missing commands."""

    def test_shipped_workflows_are_valid(self):
        out = StringIO()
        err = StringIO()
        code = None
        try:
            call_command("check_workflows", stdout=out, stderr=err)
        except SystemExit as exc:
            code = exc.code
        self.assertIsNone(code, f"workflow problems:\n{out.getvalue()}{err.getvalue()}")
        self.assertIn("valid", out.getvalue())
