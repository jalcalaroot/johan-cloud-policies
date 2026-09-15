import re
from typing import Any, Dict, List

from checkov.common.models.enums import CheckCategories, CheckResult
from checkov.terraform.checks.resource.base_resource_check import BaseResourceCheck

# plan_only, not custom_policies/azure/: same static-scan blindness as
# custom_011_scope_resource_group.py (CKV2_CUSTOM_AZURE_2), but this check
# has no equivalent name-based heuristic to fall back on - the real
# resources this would need to catch reference an
# azurerm_management_group by resource address, which has no "subscription"
# or "resource_group" substring to key off of. Verified by hand: against a
# schema-accurate synthetic plan JSON (real `terraform plan` isn't
# reproducible locally for azurerm - unlike aws, it requires real
# authentication even to plan a brand-new resource, confirmed by hand),
# scanning the RESOLVED `scope` value from a plan correctly distinguishes
# a resource-group scope, a narrower single-resource scope, a subscription
# scope, and a management-group scope - all as literal ARM ID strings,
# no unresolved reference left. See custom_policies/test/plan_only/azure/
# for the fixture and how it was built.
_MANAGEMENT_GROUP_SCOPE = re.compile(
    r"^/providers/Microsoft\.Management/managementGroups/", re.IGNORECASE
)


class NoManagementGroupScopePlan(BaseResourceCheck):
    def __init__(self) -> None:
        name = "Ensure resolved azurerm_role_assignment is not scoped to a management group"
        id = "CKV2_CUSTOM_AZURE_4"
        supported_resources = ["azurerm_role_assignment"]
        categories = [CheckCategories.IAM]
        super().__init__(name=name, id=id, categories=categories, supported_resources=supported_resources)

    def scan_resource_conf(self, conf: Dict[str, List[Any]]) -> CheckResult:
        scope_list = conf.get("scope")
        scope = scope_list[0] if scope_list else None
        if not isinstance(scope, str):
            return CheckResult.UNKNOWN

        if _MANAGEMENT_GROUP_SCOPE.match(scope.strip()):
            return CheckResult.FAILED
        return CheckResult.PASSED


check = NoManagementGroupScopePlan()
