resource "azurerm_resource_group" "example" {
  name     = "example-rg"
  location = "eastus"
}

resource "azurerm_role_assignment" "scoped_contributor" {
  scope                = azurerm_resource_group.example.id
  role_definition_name = "Contributor"
  principal_id          = "00000000-0000-0000-0000-000000000000"
}

resource "azurerm_role_assignment" "scoped_reader_literal" {
  scope                = "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/example-rg"
  role_definition_name = "Reader"
  principal_id         = "00000000-0000-0000-0000-000000000000"
}

data "azurerm_subscription" "current" {}

# Policy/Cost Management genuinely only make sense at subscription scope -
# exempted by name in custom_011, not a violation.
resource "azurerm_role_assignment" "policy_contributor" {
  scope                = data.azurerm_subscription.current.id
  role_definition_name = "Resource Policy Contributor"
  principal_id          = "00000000-0000-0000-0000-000000000000"
}

resource "azurerm_role_assignment" "cost_management_reader" {
  scope                = data.azurerm_subscription.current.id
  role_definition_name = "Cost Management Reader"
  principal_id         = "00000000-0000-0000-0000-000000000000"
}
