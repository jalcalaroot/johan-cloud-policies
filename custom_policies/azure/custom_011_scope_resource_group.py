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


class ScopeToResourceGroup(BaseResourceCheck):
    def __init__(self) -> None:
        name = "Ensure azurerm_role_assignment is not scoped directly to a subscription"
        id = "CKV2_CUSTOM_AZURE_2"
        supported_resources = ["azurerm_role_assignment"]
        categories = [CheckCategories.IAM]
        super().__init__(name=name, id=id, categories=categories, supported_resources=supported_resources)

    def scan_resource_conf(self, conf: Dict[str, List[Any]]) -> CheckResult:
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
