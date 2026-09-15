from typing import Any, Dict, List

from checkov.common.models.enums import CheckCategories, CheckResult
from checkov.common.util.type_forcers import force_list
from checkov.terraform.checks.data.base_check import BaseDataCheck

# aws_iam_policy_document is a data source, not a managed resource - needs
# BaseDataCheck/scan_data_conf/supported_data, NOT BaseResourceCheck. Using
# the wrong base class makes Checkov silently never call scan_resource_conf
# for this resource type - no error, the check just never fires. Verified
# by hand against checkov's own built-in IAMPublicActionsPolicy check
# (checkov/terraform/checks/data/aws/IAMPublicActionsPolicy.py) before
# writing this - not assumed.
#
# conf shape, verified by printing it for a real statement block:
#   conf["statement"] -> list of dicts
#   statement["actions"] -> [["s3:GetObject", ...]] (double-wrapped: outer
#     list is Checkov's generic attribute wrapper, inner list is the
#     actual Terraform list(string) value)


class NoWildcardActions(BaseDataCheck):
    def __init__(self) -> None:
        name = "Ensure IAM policy statements do not use a wildcard (*) action"
        id = "CKV2_CUSTOM_AWS_1"
        supported_data = ["aws_iam_policy_document"]
        categories = [CheckCategories.IAM]
        super().__init__(name=name, id=id, categories=categories, supported_data=supported_data)

    def scan_data_conf(self, conf: Dict[str, List[Any]]) -> CheckResult:
        statements = force_list(conf.get("statement"))
        for statement in statements:
            if not isinstance(statement, dict):
                continue
            # Deny statements with a wildcard action are a common, legitimate
            # guardrail pattern (e.g. deny everything outside an allowed
            # region) - only flag Allow.
            effect = statement.get("effect", ["Allow"])
            if effect and effect[0] == "Deny":
                continue

            actions = statement.get("actions")
            if not actions or not isinstance(actions[0], list):
                continue
            if "*" in actions[0]:
                return CheckResult.FAILED

        return CheckResult.PASSED


check = NoWildcardActions()
