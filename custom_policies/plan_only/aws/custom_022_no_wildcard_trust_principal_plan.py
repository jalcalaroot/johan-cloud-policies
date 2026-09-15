import json
from typing import Any, Dict, List

from checkov.common.models.enums import CheckCategories, CheckResult
from checkov.terraform.checks.resource.base_resource_check import BaseResourceCheck

# plan_only: same reason as custom_020/021, but for `assume_role_policy` on
# aws_iam_role instead of `policy` on a policy resource. When the trust
# policy is built with `data.aws_iam_policy_document...json` (this
# account's pattern in jalcalaroot-aws-bootstrap), the attribute is an
# unresolved reference against static HCL and never reaches PASSED/FAILED.
# Verified CKV_AWS_60 (built-in, same concern) PASSES on a literal
# Principal = "*" string, which is why this exists as a separate check
# rather than relying on it.


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


class NoWildcardTrustPrincipalPlan(BaseResourceCheck):
    def __init__(self) -> None:
        name = "Ensure resolved IAM role trust policy does not allow a wildcard Principal"
        id = "CKV2_CUSTOM_AWS_7"
        supported_resources = ["aws_iam_role"]
        categories = [CheckCategories.IAM]
        super().__init__(name=name, id=id, categories=categories, supported_resources=supported_resources)

    def scan_resource_conf(self, conf: Dict[str, List[Any]]) -> CheckResult:
        policy_list = conf.get("assume_role_policy")
        policy = _load_policy(policy_list[0]) if policy_list else None
        if policy is None:
            return CheckResult.UNKNOWN

        for statement in _as_list(policy.get("Statement")):
            if not isinstance(statement, dict) or statement.get("Effect") != "Allow":
                continue

            principal = statement.get("Principal")
            if principal == "*":
                return CheckResult.FAILED
            if isinstance(principal, dict):
                for values in principal.values():
                    if any(v == "*" for v in _as_list(values) if isinstance(v, str)):
                        return CheckResult.FAILED
        return CheckResult.PASSED


check = NoWildcardTrustPrincipalPlan()
