from typing import Any, Dict, List

from checkov.common.models.enums import CheckCategories, CheckResult
from checkov.terraform.checks.resource.base_resource_check import BaseResourceCheck


class NoOwnerAssignment(BaseResourceCheck):
    def __init__(self) -> None:
        name = "Ensure no azurerm_role_assignment grants the Owner role"
        id = "CKV2_CUSTOM_AZURE_1"
        supported_resources = ["azurerm_role_assignment"]
        categories = [CheckCategories.IAM]
        super().__init__(name=name, id=id, categories=categories, supported_resources=supported_resources)

    def scan_resource_conf(self, conf: Dict[str, List[Any]]) -> CheckResult:
        role = conf.get("role_definition_name")
        if role and role[0] and str(role[0]).strip().lower() == "owner":
            return CheckResult.FAILED
        return CheckResult.PASSED


check = NoOwnerAssignment()
