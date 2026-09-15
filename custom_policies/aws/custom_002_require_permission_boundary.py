from typing import Any, Dict, List

from checkov.common.models.enums import CheckCategories, CheckResult
from checkov.terraform.checks.resource.base_resource_check import BaseResourceCheck

# aws_iam_role is a managed resource, so BaseResourceCheck/scan_resource_conf
# is correct here (unlike aws_iam_policy_document, a data source - see
# custom_001 for why that distinction matters).


class RequirePermissionBoundary(BaseResourceCheck):
    def __init__(self) -> None:
        name = "Ensure IAM roles have a permissions boundary attached"
        id = "CKV2_CUSTOM_AWS_2"
        supported_resources = ["aws_iam_role"]
        categories = [CheckCategories.IAM]
        super().__init__(name=name, id=id, categories=categories, supported_resources=supported_resources)

    def scan_resource_conf(self, conf: Dict[str, List[Any]]) -> CheckResult:
        boundary = conf.get("permissions_boundary")
        if boundary and boundary[0]:
            return CheckResult.PASSED
        return CheckResult.FAILED


check = RequirePermissionBoundary()
