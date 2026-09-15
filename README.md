# johan-cloud-policies

Custom [Checkov](https://github.com/bridgecrewio/checkov) checks for house rules that Checkov's ~1000 built-in policies can't know about — this account's own IAM/RBAC conventions, not general best practices. Shared across every repo here that runs Checkov, so a rule is written once instead of copy-pasted per repo.

## Why Python, not YAML

Checkov supports custom checks in both YAML and Python via `--external-checks-dir`. Tried YAML first, by hand, straight from Checkov's own documented example — it silently never loaded (0 findings, no error). This isn't a config mistake on this repo's part: it's a known, multi-year open upstream issue ([bridgecrewio/checkov#1162](https://github.com/bridgecrewio/checkov/issues/1162), [#4930](https://github.com/bridgecrewio/checkov/issues/4930), [#5234](https://github.com/bridgecrewio/checkov/issues/5234), [#5444](https://github.com/bridgecrewio/checkov/issues/5444)).

Python custom checks **do** load correctly via `--external-checks-dir` — but only with an undocumented requirement, also found by hand: the directory needs an `__init__.py` (even an empty one) alongside the check files, or Checkov silently loads nothing, same symptom as the YAML bug. Every subdirectory here has one for that reason.

## Checks

| ID | File | Provider | What it checks |
|---|---|---|---|
| `CKV2_CUSTOM_AWS_1` | `custom_policies/aws/custom_001_no_wildcard_actions.py` | AWS | No `data.aws_iam_policy_document` statement uses a wildcard (`*`) `Action` — `Deny` statements are exempt (a wildcard on `Deny` is a legitimate guardrail pattern, not an escalation risk) |
| `CKV2_CUSTOM_AWS_3` | `custom_policies/aws/custom_003_iam_role_required_tags.py` | AWS | Every `aws_iam_role` has `Owner` and `Environment` tags |
| `CKV2_CUSTOM_AWS_4` | `custom_policies/aws/custom_004_no_admin_managed_policy.py` | AWS | No policy attachment uses `AdministratorAccess`/`PowerUserAccess`/`IAMFullAccess` (built-in `CKV_AWS_274` only covers the first one) |
| `CKV2_CUSTOM_AZURE_1` | `custom_policies/azure/custom_010_no_privileged_role_assignment.py` | Azure | No `azurerm_role_assignment` grants `Owner`, `User Access Administrator`, or `Role Based Access Control Administrator` — the roles that can themselves grant further access. `Contributor` is deliberately excluded; see the file's own comment |
| `CKV2_CUSTOM_AZURE_2` | `custom_policies/azure/custom_011_scope_resource_group.py` | Azure | No `azurerm_role_assignment` is scoped directly to a subscription, except a small allowlist of roles (Policy, Cost Management) that are near-exclusively meaningful at that scope — see the file's own comments. Best-effort, not exhaustive: Checkov shows the raw unresolved `scope` expression, not the resolved ARM ID |
| `CKV2_CUSTOM_AZURE_3` | `custom_policies/azure/custom_012_required_tags.py` | Azure | Every `azurerm_resource_group`/`azurerm_key_vault`/`azurerm_storage_account` has `Owner` and `Environment` tags |

Verified against this account's real repos before wiring any of these in. `custom_001` and the original `custom_010` (then Owner-only) passed cleanly everywhere with zero changes needed. `custom_011` found one real, ambiguous case in `jalcalaroot-azure-bootstrap` (`dev_plan` needs `Reader` at subscription scope to plan across every resource group, not the more common single-RG case this check is meant to catch) — deliberately left failing rather than silently exempted, since "Reader" is too generic a role name to blanket-exempt without also hiding a real overscoping mistake elsewhere. That one needs an inline `#checkov:skip` with its own justification in the consuming repo, same as any other accepted Checkov exception in this account. `custom_003`/`custom_004`/`custom_012` found real, currently-untagged/unreviewed resources across `aws-eks-cluster`, `jalcalaroot-aws-bootstrap`, and `azure-aks-cluster` — expected findings for a rule enforcing a convention that didn't exist yet, not false positives.

## `custom_policies/plan_only/`

Checks that only evaluate correctly against a **resolved Terraform plan** (`checkov -f plan.json`), never against static HCL (`checkov -d .`). Kept out of `custom_policies/aws/`/`azure/` for the same reason `draft/` is separate: pointing a repo's *static* Checkov step at the whole provider folder would silently load these too, and they'd never fire there — worse than not having them, because it looks covered and isn't.

Root cause, found by hand while validating a batch of pasted third-party rules against this account's real repos: every one of them reads a resource attribute (an IAM policy JSON, a role assignment's `scope`) that this account's real Terraform **always** sets via a cross-resource reference (`data.aws_iam_policy_document.x.json`, `azurerm_resource_group.x.id`) rather than a literal. Checkov's static HCL scan hands the check the raw, unresolved reference string — confirmed with a debug check dumping `repr(conf.get(...))`, e.g. `['data.aws_iam_policy_document.dev_agent_permissions.json']`, never a dict. The check doesn't error, it just never reaches PASSED/FAILED for that resource — silently absent from the report, same failure mode as the missing-`__init__.py` and YAML bugs above. Against the resolved plan, Terraform has already inlined the real value, and the exact same check logic works correctly — verified with a real `terraform plan` (AWS, using `skip_credentials_validation`) for the AWS checks, and a schema-accurate synthetic plan JSON for the Azure one (`azurerm` requires real authentication even to plan a brand-new resource — no static-fixture equivalent to AWS's escape hatch; see `custom_policies/test/plan_only/azure/README.md`).

| ID | File | Provider | What it checks |
|---|---|---|---|
| `CKV2_CUSTOM_AWS_5` | `custom_policies/plan_only/aws/custom_020_no_wildcard_actions_plan.py` | AWS | Resolved IAM policy has no wildcard (`*`, `service:*`) `Allow` action |
| `CKV2_CUSTOM_AWS_6` | `custom_policies/plan_only/aws/custom_021_no_passrole_wildcard_plan.py` | AWS | Resolved IAM policy doesn't grant `iam:PassRole` with an unconditioned `Resource "*"` — a `Condition` clause (e.g. `iam:PassedToService`, this account's actual pattern) is treated as scoped, not a violation |
| `CKV2_CUSTOM_AWS_7` | `custom_policies/plan_only/aws/custom_022_no_wildcard_trust_principal_plan.py` | AWS | Resolved IAM role trust policy (`assume_role_policy`) doesn't allow a wildcard `Principal` |
| `CKV2_CUSTOM_AZURE_4` | `custom_policies/plan_only/azure/custom_023_no_management_group_scope_plan.py` | Azure | Resolved `azurerm_role_assignment` isn't scoped to a management group. (Subscription scope is already covered statically by `CKV2_CUSTOM_AZURE_2` via a name-based heuristic that doesn't need plan resolution — no equivalent heuristic exists for management groups, so this one needs the plan) |

These need `gha-checkov-plan-scan`'s `external_checks_dirs` support (see its own README) to actually run in a consuming repo — the plan-scan step, not the static Checkov step. Because that step is non-blocking (`soft-fail`, for the unrelated `#checkov:skip`-in-plan-mode bug documented there), findings from these 4 checks are currently informational only, same as everything else in that step.

## `custom_policies/draft/`

Checks that are written and self-tested but **not yet referenced by any consuming repo's `external_checks_dirs`** — kept here instead of deleted so the work isn't lost, and kept out of `custom_policies/aws/`\`azure/` specifically because pointing a repo at the whole provider folder loads every file in it; a draft check sitting next to the active ones would go live the moment anyone bumps the pinned SHA, with no explicit decision to do so.

| ID | File | Why it's a draft, not active |
|---|---|---|
| `CKV2_CUSTOM_AWS_2` | `custom_policies/draft/aws/custom_002_require_permission_boundary.py` (every `aws_iam_role` must set `permissions_boundary`) | Verified against this account's real repos: **fails on all 9 existing IAM roles** across `aws-eks-cluster` and `jalcalaroot-aws-bootstrap` — none has a permission boundary today. Adding one for real is an infrastructure change (a boundary policy has to exist and be referenced), not something to flip on as blocking without that work happening first. |

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

`custom_policies/test/run_tests.py` runs every check above against its own `good/`/`bad/` fixture and asserts the expected outcome — zero failures on `good/`, at least one on `bad/`. Three fixture shapes:

- Static checks (`custom_policies/aws/`, `azure/`, `draft/`): Terraform fixtures (`custom_policies/test/<provider>/{good,bad}/main.tf`), scanned directly with `checkov -d`.
- `plan_only/aws/`: Terraform fixtures too, but the script runs a real `terraform init`/`plan`/`show -json` against them first (AWS's `skip_credentials_validation`, no real cloud credentials) and scans the resulting plan JSON.
- `plan_only/azure/`: pre-built plan JSON (`custom_policies/test/plan_only/azure/{good,bad}.json`) — `azurerm` has no equivalent to AWS's escape hatch, see that directory's own README.

`.github/workflows/test.yml` installs a pinned Checkov and Terraform and runs the whole suite on every push/PR.
