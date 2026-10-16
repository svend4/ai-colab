#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Регрессия D-026 П-4: массовое удаление одобряет человек через GitHub Environment, а не токен
в сообщении коммита или метка на PR. Тест фиксирует отсутствие обходных маркеров в bulk-guard.yml
и наличие job mass-delete-approval, который зависит от вывода bulk-guard (см. D-040)."""
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
WORKFLOW = os.path.join(ROOT, ".github", "workflows", "bulk-guard.yml")

BYPASS_MARKERS = ("allow-mass-delete", "D-026 accepted:", "bulk-approved")


class BulkGuardWorkflowTest(unittest.TestCase):
    def setUp(self):
        with open(WORKFLOW, encoding="utf-8") as f:
            self.text = f.read()

    def test_no_commit_message_bypass_markers(self):
        for marker in BYPASS_MARKERS:
            with self.subTest(marker=marker):
                self.assertNotIn(marker, self.text)

    def test_approval_goes_through_environment(self):
        self.assertIn("mass-delete-approval:", self.text)
        self.assertIn("environment: mass-delete-approval", self.text)
        self.assertIn("needs: bulk-guard", self.text)
        self.assertIn("if: needs.bulk-guard.outputs.mass_delete == 'true'", self.text)

    def test_guard_publishes_mass_delete_output(self):
        self.assertIn("mass_delete: ${{ steps.range.outputs.mass_delete }}", self.text)
        self.assertIn('echo "mass_delete=true" >> "$GITHUB_OUTPUT"', self.text)


if __name__ == "__main__":
    unittest.main()
