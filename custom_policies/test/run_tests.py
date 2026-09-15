#!/usr/bin/env python3
"""Self-test for the custom checks: each one must FAIL on its `bad/`
fixture and PASS (with zero failures) on its `good/` fixture. Run locally
with the repo's checkov already installed, or via .github/workflows/test.yml.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent  # repo root
POLICIES = ROOT / "custom_policies"
TEST = POLICIES / "test"

CASES = [
    ("CKV2_CUSTOM_AWS_1", POLICIES / "aws", TEST / "aws" / "bad", TEST / "aws" / "good"),
    ("CKV2_CUSTOM_AWS_2", POLICIES / "aws", TEST / "aws" / "bad", TEST / "aws" / "good"),
    ("CKV2_CUSTOM_AZURE_1", POLICIES / "azure", TEST / "azure" / "bad", TEST / "azure" / "good"),
    ("CKV2_CUSTOM_AZURE_2", POLICIES / "azure", TEST / "azure" / "bad", TEST / "azure" / "good"),
]


def run_checkov(directory: Path, external_checks_dir: Path, check_id: str) -> dict:
    result = subprocess.run(
        [
            "checkov",
            "-d", str(directory),
            "--external-checks-dir", str(external_checks_dir),
            "--check", check_id,
            "-o", "json",
            "--compact",
        ],
        capture_output=True,
        text=True,
    )
    # checkov exits non-zero when there are failed checks - that's expected
    # for the "bad" fixtures, so don't check the return code here.
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"Could not parse checkov output as JSON.\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        sys.exit(1)


def count_results(report: dict, check_id: str, outcome: str) -> int:
    checks = report.get("results", {}).get(f"{outcome}_checks", [])
    return sum(1 for c in checks if c.get("check_id") == check_id)


def main() -> int:
    failures = []

    for check_id, external_dir, bad_dir, good_dir in CASES:
        bad_report = run_checkov(bad_dir, external_dir, check_id)
        good_report = run_checkov(good_dir, external_dir, check_id)

        bad_failed = count_results(bad_report, check_id, "failed")
        good_failed = count_results(good_report, check_id, "failed")
        good_passed = count_results(good_report, check_id, "passed")

        if bad_failed < 1:
            failures.append(f"{check_id}: expected at least 1 failure in {bad_dir}, got {bad_failed}")
        if good_failed != 0:
            failures.append(f"{check_id}: expected 0 failures in {good_dir}, got {good_failed}")
        if good_passed < 1:
            failures.append(f"{check_id}: expected at least 1 pass in {good_dir}, got {good_passed}")

        print(f"{check_id}: bad_failed={bad_failed} good_failed={good_failed} good_passed={good_passed}")

    if failures:
        print("\nFAILURES:")
        for f in failures:
            print(f" - {f}")
        return 1

    print("\nAll custom checks behave as expected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
