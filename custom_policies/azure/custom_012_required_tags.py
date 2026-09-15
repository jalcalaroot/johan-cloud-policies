from typing import Any, Dict, List

from checkov.common.models.enums import CheckCategories, CheckResult
from checkov.terraform.checks.resource.base_resource_check import BaseResourceCheck


class AzureRequiredTags(BaseResourceCheck):
    def __init__(self) -> None:
        name = "Ensure resource group / key vault / storage account has Owner and Environment tags"
        id = "CKV2_CUSTOM_AZURE_3"
        supported_resources = [
            "azurerm_resource_group",
            "azurerm_key_vault",
            "azurerm_storage_account",
        ]
        categories = [CheckCategories.GENERAL_SECURITY]
        super().__init__(name=name, id=id, categories=categories, supported_resources=supported_resources)

    def scan_resource_conf(self, conf: Dict[str, List[Any]]) -> CheckResult:
        tags_list = conf.get("tags")
        tags = tags_list[0] if tags_list else None
        if not isinstance(tags, dict):
            return CheckResult.FAILED

        owner = tags.get("Owner")
        environment = tags.get("Environment")
        if owner and str(owner).strip() and environment and str(environment).strip():
            return CheckResult.PASSED
        return CheckResult.FAILED


check = AzureRequiredTags()
