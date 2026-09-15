#!/usr/bin/env python3
"""Self-test for the custom checks: each one must FAIL on its `bad/`
fixture and PASS (with zero failures) on its `good/` fixture. Run locally
with the repo's checkov already installed, or via .github/workflows/test.yml.

Two kinds of cases:
- CASES: static HCL fixtures, scanned directly with `checkov -d`.
- PLAN_DIR_CASES: HCL fixtures that only resolve correctly against a
  Terraform plan (see custom_policies/plan_only/ - the check itself reads
  a resource attribute, like an IAM policy JSON or a role-assignment
  scope, that this account's real repos always set via a cross-resource
  reference. Static HCL scanning sees the unresolved reference string,
  not the value). `terraform init`/`plan`/`show -json` runs against the
  fixture first, using AWS's skip_credentials_validation escape hatch -
  no real cloud credentials involved.
- PLAN_FILE_CASES: pre-built plan JSON fixtures, for providers (azurerm)
  that don't support planning without real authentication even for
  brand-new resources - see custom_policies/test/plan_only/azure/README.md.
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
    ("CKV2_CUSTOM_AWS_3", POLICIES / "aws", TEST / "aws" / "bad", TEST / "aws" / "good"),
    ("CKV2_CUSTOM_AWS_4", POLICIES / "aws", TEST / "aws" / "bad", TEST / "aws" / "good"),
    ("CKV2_CUSTOM_AZURE_1", POLICIES / "azure", TEST / "azure" / "bad", TEST / "azure" / "good"),
    ("CKV2_CUSTOM_AZURE_2", POLICIES / "azure", TEST / "azure" / "bad", TEST / "azure" / "good"),
    ("CKV2_CUSTOM_AZURE_3", POLICIES / "azure", TEST / "azure" / "bad", TEST / "azure" / "good"),
    # Draft: written and tested, but NOT referenced by any consuming repo's
    # external_checks_dirs yet - see custom_policies/draft/aws/README below.
    ("CKV2_CUSTOM_AWS_2", POLICIES / "draft" / "aws", TEST / "draft" / "aws" / "bad", TEST / "draft" / "aws" / "good"),
]

PLAN_DIR_CASES = [
    ("CKV2_CUSTOM_AWS_5", POLICIES / "plan_only" / "aws", TEST / "plan_only" / "aws" / "bad", TEST / "plan_only" / "aws" / "good"),
    ("CKV2_CUSTOM_AWS_6", POLICIES / "plan_only" / "aws", TEST / "plan_only" / "aws" / "bad", TEST / "plan_only" / "aws" / "good"),
    ("CKV2_CUSTOM_AWS_7", POLICIES / "plan_only" / "aws", TEST / "plan_only" / "aws" / "bad", TEST / "plan_only" / "aws" / "good"),
]

PLAN_FILE_CASES = [
    (
        "CKV2_CUSTOM_AZURE_4",
        POLICIES / "plan_only" / "azure",
        TEST / "plan_only" / "azure" / "bad.json",
        TEST / "plan_only" / "azure" / "good.json",
    ),
]


def run_checkov(args: list, check_id: str) -> dict:
    result = subprocess.run(
        ["checkov", *args, "--check", check_id, "-o", "json", "--compact"],
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


def run_checkov_dir(directory: Path, external_checks_dir: Path, check_id: str) -> dict:
    return run_checkov(["-d", str(directory), "--external-checks-dir", str(external_checks_dir)], check_id)


def run_checkov_plan_file(plan_file: Path, external_checks_dir: Path, check_id: str) -> dict:
    return run_checkov(["-f", str(plan_file), "--external-checks-dir", str(external_checks_dir)], check_id)


def terraform_plan_json(directory: Path) -> Path:
    """Run terraform init/plan against `directory` and return the plan.json path."""
    plan_bin = directory / "tfplan"
    plan_json = directory / "plan.json"

    subprocess.run(["terraform", "init", "-input=false", "-no-color"], cwd=directory, check=True, capture_output=True)
    subprocess.run(
        ["terraform", "plan", "-input=false", "-no-color", f"-out={plan_bin.name}"],
        cwd=directory,
        check=True,
        capture_output=True,
    )
    show = subprocess.run(
        ["terraform", "show", "-json", plan_bin.name],
        cwd=directory,
        check=True,
        capture_output=True,
        text=True,
    )
    plan_json.write_text(show.stdout)
    return plan_json


def count_results(report: dict, check_id: str, outcome: str) -> int:
    checks = report.get("results", {}).get(f"{outcome}_checks", [])
    return sum(1 for c in checks if c.get("check_id") == check_id)


def evaluate(check_id: str, bad_report: dict, good_report: dict, failures: list) -> None:
    bad_failed = count_results(bad_report, check_id, "failed")
    good_failed = count_results(good_report, check_id, "failed")
    good_passed = count_results(good_report, check_id, "passed")

    if bad_failed < 1:
        failures.append(f"{check_id}: expected at least 1 failure on the bad fixture, got {bad_failed}")
    if good_failed != 0:
        failures.append(f"{check_id}: expected 0 failures on the good fixture, got {good_failed}")
    if good_passed < 1:
        failures.append(f"{check_id}: expected at least 1 pass on the good fixture, got {good_passed}")

    print(f"{check_id}: bad_failed={bad_failed} good_failed={good_failed} good_passed={good_passed}")


def main() -> int:
    failures: list = []

    for check_id, external_dir, bad_dir, good_dir in CASES:
        bad_report = run_checkov_dir(bad_dir, external_dir, check_id)
        good_report = run_checkov_dir(good_dir, external_dir, check_id)
        evaluate(check_id, bad_report, good_report, failures)

    plan_dirs_done: dict = {}
    for check_id, external_dir, bad_dir, good_dir in PLAN_DIR_CASES:
        if bad_dir not in plan_dirs_done:
            plan_dirs_done[bad_dir] = terraform_plan_json(bad_dir)
        if good_dir not in plan_dirs_done:
            plan_dirs_done[good_dir] = terraform_plan_json(good_dir)

        bad_report = run_checkov_plan_file(plan_dirs_done[bad_dir], external_dir, check_id)
        good_report = run_checkov_plan_file(plan_dirs_done[good_dir], external_dir, check_id)
        evaluate(check_id, bad_report, good_report, failures)

    for check_id, external_dir, bad_file, good_file in PLAN_FILE_CASES:
        bad_report = run_checkov_plan_file(bad_file, external_dir, check_id)
        good_report = run_checkov_plan_file(good_file, external_dir, check_id)
        evaluate(check_id, bad_report, good_report, failures)

    if failures:
        print("\nFAILURES:")
        for f in failures:
            print(f" - {f}")
        return 1

    print("\nAll custom checks behave as expected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
