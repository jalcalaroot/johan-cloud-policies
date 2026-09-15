import re
from typing import Any, Dict, List

from checkov.common.models.enums import CheckCategories, CheckResult
from checkov.terraform.checks.resource.base_resource_check import BaseResourceCheck

# Best-effort, not exhaustive: verified by hand that Checkov shows the raw
# UNRESOLVED HCL expression for `scope` when it's a reference (e.g.
# "data.azurerm_subscription.current.id"), not the resolved ARM ID - there
# is no way to statically know the real scope in that case. This check
# combines an exact match for a literal subscription-root ARM ID with a
# name-based heuristic for the common reference pattern; it will not catch
# every way to construct a subscription-scoped assignment (e.g. through an
# intermediate local or module output with no "subscription"/"resource_group"
# in its own name).
_SUBSCRIPTION_ROOT = re.compile(r"^/subscriptions/[^/]+$")

# Some Azure built-in roles are near-exclusively meaningful at subscription
# (or management group) scope for a single-subscription account like this
# one - Policy assignment and Cost Management don't have a resource-group
# equivalent that does the same job. Verified against real usage in
# jalcalaroot-azure-bootstrap/terraform/environments/dev/identities.tf
# (dev_agent_policy_contributor, dev_agent_cost_management_contributor,
# dev_plan_cost_management_reader) before adding this exemption - these are
# genuine subscription-scoped needs, not a rule loophole.
#
# Deliberately NOT exempted: generic roles like "Reader" or "Contributor"
# CAN legitimately need subscription scope (e.g. a plan role that reads
# state across every resource group), but are just as commonly
# resource-group-scoped - there's no name-based way to tell those apart
# safely. A genuinely-needed subscription-scoped "Reader" should get an
# inline #checkov:skip with its own justification, same as any other
# accepted Checkov exception in this account's repos, rather than a
# blanket exemption here that would also hide a real overscoping mistake.
_SUBSCRIPTION_SCOPED_ROLES = {
    "policy contributor",
    "resource policy contributor",
    "policy reader",
    "cost management contributor",
    "cost management reader",
}


class ScopeToResourceGroup(BaseResourceCheck):
    def __init__(self) -> None:
        name = "Ensure azurerm_role_assignment is not scoped directly to a subscription"
        id = "CKV2_CUSTOM_AZURE_2"
        supported_resources = ["azurerm_role_assignment"]
        categories = [CheckCategories.IAM]
        super().__init__(name=name, id=id, categories=categories, supported_resources=supported_resources)

    def scan_resource_conf(self, conf: Dict[str, List[Any]]) -> CheckResult:
        role = conf.get("role_definition_name")
        if role and role[0] and str(role[0]).strip().lower() in _SUBSCRIPTION_SCOPED_ROLES:
            return CheckResult.PASSED

        scope = conf.get("scope")
        if not scope or not scope[0]:
            return CheckResult.PASSED

        scope_val = str(scope[0])

        if _SUBSCRIPTION_ROOT.fullmatch(scope_val):
            return CheckResult.FAILED

        lowered = scope_val.lower()
        if "subscription" in lowered and "resource_group" not in lowered and "resourcegroup" not in lowered:
            return CheckResult.FAILED

        return CheckResult.PASSED


check = ScopeToResourceGroup()
