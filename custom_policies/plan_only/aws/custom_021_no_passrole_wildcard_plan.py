import json
from typing import Any, Dict, List

from checkov.common.models.enums import CheckCategories, CheckResult
from checkov.terraform.checks.resource.base_resource_check import BaseResourceCheck

# plan_only: same reason as custom_020 - "policy" is an unresolved
# `data.aws_iam_policy_document...json` reference against static HCL in
# this account's real repos, only resolved against the Terraform plan.
#
# iam:PassRole with Resource "*" is the most common AWS privilege
# escalation path: it lets the caller hand ANY role in the account to a
# service it controls. A real, scoped use of PassRole restricts Resource
# to the specific role ARN(s) it's meant to pass (see e.g.
# jalcalaroot-aws-bootstrap's PassFlowLogsRole statement, which is fine and
# won't trip this - it's scoped by iam:PassedToService condition, but
# Resource itself is still "*" there... this check only flags the
# combination of PassRole + a completely open Resource with no condition
# clause narrowing it, which the real statement doesn't have. Verified by
# hand against jalcalaroot-aws-bootstrap's actual PassFlowLogsRole
# statement before finalizing this - it does NOT trigger a false positive
# there, because a condition is present.
_POLICY_RESOURCES = [
    "aws_iam_policy",
    "aws_iam_role_policy",
    "aws_iam_group_policy",
    "aws_iam_user_policy",
]


def _load_policy(raw: Any) -> Dict[str, Any] | None:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except (ValueError, TypeError):
            return None
    return None


def _as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


class NoPassRoleWildcardPlan(BaseResourceCheck):
    def __init__(self) -> None:
        name = "Ensure resolved IAM policy does not grant iam:PassRole with an unconditioned Resource *"
        id = "CKV2_CUSTOM_AWS_6"
        supported_resources = _POLICY_RESOURCES
        categories = [CheckCategories.IAM]
        super().__init__(name=name, id=id, categories=categories, supported_resources=supported_resources)

    def scan_resource_conf(self, conf: Dict[str, List[Any]]) -> CheckResult:
        policy_list = conf.get("policy")
        policy = _load_policy(policy_list[0]) if policy_list else None
        if policy is None:
            return CheckResult.UNKNOWN

        for statement in _as_list(policy.get("Statement")):
            if not isinstance(statement, dict) or statement.get("Effect") != "Allow":
                continue

            actions = [a for a in _as_list(statement.get("Action")) if isinstance(a, str)]
            if not any(a in ("iam:PassRole", "iam:*", "*") for a in actions):
                continue

            # A condition clause (e.g. iam:PassedToService) narrows an
            # otherwise-open Resource "*" to a specific real-world use -
            # that's the account's actual pattern, not a false positive to
            # paper over.
            if statement.get("Condition"):
                continue

            resources = [r for r in _as_list(statement.get("Resource")) if isinstance(r, str)]
            if any(r == "*" for r in resources):
                return CheckResult.FAILED
        return CheckResult.PASSED


check = NoPassRoleWildcardPlan()
