from typing import Any, Dict, List

from checkov.common.models.enums import CheckCategories, CheckResult
from checkov.terraform.checks.resource.base_resource_check import BaseResourceCheck

# CKV_AWS_274 (built-in) only blocks AdministratorAccess. This adds the two
# other AWS-managed policies that grant equivalent or IAM-escalation-capable
# access: PowerUserAccess (everything except IAM/Organizations, still wide
# open for data access) and IAMFullAccess (can attach any policy to any
# principal, including itself - a direct escalation path).
_ADMIN_POLICY_ARNS = {
    "arn:aws:iam::aws:policy/AdministratorAccess",
    "arn:aws:iam::aws:policy/PowerUserAccess",
    "arn:aws:iam::aws:policy/IAMFullAccess",
}


class NoAdminManagedPolicy(BaseResourceCheck):
    def __init__(self) -> None:
        name = "Ensure no IAM policy attachment uses AdministratorAccess/PowerUserAccess/IAMFullAccess"
        id = "CKV2_CUSTOM_AWS_4"
        supported_resources = [
            "aws_iam_role_policy_attachment",
            "aws_iam_group_policy_attachment",
            "aws_iam_user_policy_attachment",
        ]
        categories = [CheckCategories.IAM]
        super().__init__(name=name, id=id, categories=categories, supported_resources=supported_resources)

    def scan_resource_conf(self, conf: Dict[str, List[Any]]) -> CheckResult:
        arn = conf.get("policy_arn")
        if arn and arn[0] and str(arn[0]).strip() in _ADMIN_POLICY_ARNS:
            return CheckResult.FAILED
        return CheckResult.PASSED


check = NoAdminManagedPolicy()
