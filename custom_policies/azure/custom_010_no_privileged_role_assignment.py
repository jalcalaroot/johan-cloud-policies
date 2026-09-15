from typing import Any, Dict, List

from checkov.common.models.enums import CheckCategories, CheckResult
from checkov.terraform.checks.resource.base_resource_check import BaseResourceCheck

# "Contributor" is deliberately NOT in this set. It's the standard role for
# a CI automation identity that manages resources within one resource group
# or a single resource (see e.g. jalcalaroot-azure-bootstrap's dev_agent,
# azure-aks-cluster's ci_agent/AGIC) - Azure explicitly excludes
# Microsoft.Authorization/roleAssignments/write from Contributor, so it
# can't grant access to anyone. Owner, User Access Administrator and Role
# Based Access Control Administrator all can - that's the actual
# escalation risk this check exists to catch. Verified against real usage
# in azure-aks-cluster/ci_identities.tf: adding "Contributor" here would
# fail two legitimate, already-justified automation role assignments
# (ci_agent_rg_contributor, agic_app_gateway_contributor) with no
# escalation risk to show for it.
_PRIVILEGED_ROLES = {
    "owner",
    "user access administrator",
    "role based access control administrator",
}


class NoPrivilegedRoleAssignment(BaseResourceCheck):
    def __init__(self) -> None:
        name = "Ensure no azurerm_role_assignment grants Owner/User Access Administrator/RBAC Administrator"
        id = "CKV2_CUSTOM_AZURE_1"
        supported_resources = ["azurerm_role_assignment"]
        categories = [CheckCategories.IAM]
        super().__init__(name=name, id=id, categories=categories, supported_resources=supported_resources)

    def scan_resource_conf(self, conf: Dict[str, List[Any]]) -> CheckResult:
        role = conf.get("role_definition_name")
        if role and role[0] and str(role[0]).strip().lower() in _PRIVILEGED_ROLES:
            return CheckResult.FAILED
        return CheckResult.PASSED


check = NoPrivilegedRoleAssignment()
