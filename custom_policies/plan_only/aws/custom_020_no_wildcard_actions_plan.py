import json
from typing import Any, Dict, List

from checkov.common.models.enums import CheckCategories, CheckResult
from checkov.terraform.checks.resource.base_resource_check import BaseResourceCheck

# plan_only, not custom_policies/aws/: this repo's real IAM policies are
# built with `data.aws_iam_policy_document ... .json`, not inline
# jsonencode(). Verified by hand (debug check dumping raw conf) that
# against static HCL, the "policy" attribute on the resource comes through
# as the UNRESOLVED reference string
# (e.g. "data.aws_iam_policy_document.dev_agent_permissions.json"), never
# a JSON dict/string - so this check would silently never fire (not even
# UNKNOWN, just absent from the report) against every real repo in this
# account. Against a resolved plan (`checkov -f plan.json`), Terraform has
# already inlined the actual policy JSON into the resource's `policy`
# value - confirmed with a real `terraform plan` fixture reproducing this
# exact pattern (see gha-checkov-plan-scan, which is how this gets run in
# CI: the plan-scan step, not the static Checkov step).
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


class NoWildcardActionsPlan(BaseResourceCheck):
    def __init__(self) -> None:
        name = "Ensure resolved IAM policy has no wildcard (*, service:*) Allow actions"
        id = "CKV2_CUSTOM_AWS_5"
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
            for action in _as_list(statement.get("Action")):
                if isinstance(action, str) and (action == "*" or action.endswith(":*")):
                    return CheckResult.FAILED
        return CheckResult.PASSED


check = NoWildcardActionsPlan()
