data "azurerm_subscription" "current" {}

resource "azurerm_role_assignment" "owner_assignment" {
  scope                = "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/example-rg"
  role_definition_name = "Owner"
  principal_id          = "00000000-0000-0000-0000-000000000000"
}

resource "azurerm_role_assignment" "subscription_scoped" {
  scope                = data.azurerm_subscription.current.id
  role_definition_name = "Contributor"
  principal_id         = "00000000-0000-0000-0000-000000000000"
}

resource "azurerm_role_assignment" "subscription_root_literal" {
  scope                = "/subscriptions/00000000-0000-0000-0000-000000000000"
  role_definition_name = "Reader"
  principal_id          = "00000000-0000-0000-0000-000000000000"
}

resource "azurerm_role_assignment" "rbac_admin_assignment" {
  scope                = "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/example-rg"
  role_definition_name = "Role Based Access Control Administrator"
  principal_id         = "00000000-0000-0000-0000-000000000000"
}

resource "azurerm_resource_group" "untagged" {
  name     = "example-untagged-rg"
  location = "eastus"
}
