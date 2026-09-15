# johan-cloud-policies

Custom [Checkov](https://github.com/bridgecrewio/checkov) checks for house rules that Checkov's ~1000 built-in policies can't know about — this account's own IAM/RBAC conventions, not general best practices. Shared across every repo here that runs Checkov, so a rule is written once instead of copy-pasted per repo.

## Why Python, not YAML

Checkov supports custom checks in both YAML and Python via `--external-checks-dir`. Tried YAML first, by hand, straight from Checkov's own documented example — it silently never loaded (0 findings, no error). This isn't a config mistake on this repo's part: it's a known, multi-year open upstream issue ([bridgecrewio/checkov#1162](https://github.com/bridgecrewio/checkov/issues/1162), [#4930](https://github.com/bridgecrewio/checkov/issues/4930), [#5234](https://github.com/bridgecrewio/checkov/issues/5234), [#5444](https://github.com/bridgecrewio/checkov/issues/5444)).

Python custom checks **do** load correctly via `--external-checks-dir` — but only with an undocumented requirement, also found by hand: the directory needs an `__init__.py` (even an empty one) alongside the check files, or Checkov silently loads nothing, same symptom as the YAML bug. Every subdirectory here has one for that reason.

## Checks

| ID | File | Provider | What it checks |
|---|---|---|---|
| `CKV2_CUSTOM_AWS_1` | `custom_policies/aws/custom_001_no_wildcard_actions.py` | AWS | No `data.aws_iam_policy_document` statement uses a wildcard (`*`) `Action` — `Deny` statements are exempt (a wildcard on `Deny` is a legitimate guardrail pattern, not an escalation risk) |
| `CKV2_CUSTOM_AWS_2` | `custom_policies/aws/custom_002_require_permission_boundary.py` | AWS | Every `aws_iam_role` has `permissions_boundary` set |
| `CKV2_CUSTOM_AZURE_1` | `custom_policies/azure/custom_010_no_owner_assignment.py` | Azure | No `azurerm_role_assignment` grants the built-in `Owner` role |
| `CKV2_CUSTOM_AZURE_2` | `custom_policies/azure/custom_011_scope_resource_group.py` | Azure | No `azurerm_role_assignment` is scoped directly to a subscription — best-effort; see the caveat in the file's own comments about unresolved `scope` expressions |

## Usage

Consuming repos need two things added to their existing Checkov step: a checkout of this repo into a subdirectory, and `external_checks_dirs` pointed at the relevant provider folder.

```yaml
- name: Checkout custom policies
  uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
  with:
    repository: jalcalaroot/johan-cloud-policies
    path: .johan-cloud-policies
    ref: <pinned-sha>

- name: Checkov
  uses: bridgecrewio/checkov-action@<pinned-sha>
  with:
    directory: .
    framework: terraform
    external_checks_dirs: .johan-cloud-policies/custom_policies/aws # or azure
    soft_fail: false
    # ...whatever other inputs the repo already uses
```

This plugs into the **existing** static Checkov step already blocking in every repo here — it's not a separate pass. A finding from one of these checks fails the build the same way a built-in Checkov finding does.

## Architecture: this repo doesn't run anything itself

Same model as [`gha-iam-policy-autopilot`](https://github.com/jalcalaroot/gha-iam-policy-autopilot) and [`gha-checkov-plan-scan`](https://github.com/jalcalaroot/gha-checkov-plan-scan): this is not a central service. It's just where the check code lives. A consuming repo checks it out and Checkov loads it **inside that repo's own job** — same runner, same permissions as the rest of that pipeline.

## Test

`custom_policies/test/run_tests.py` runs every check above against its own `good/`/`bad/` Terraform fixture (`custom_policies/test/<provider>/{good,bad}/main.tf`) and asserts the expected outcome — a check must find zero failures on `good/` and at least one on `bad/`. `.github/workflows/test.yml` installs a pinned Checkov and runs it on every push/PR.
