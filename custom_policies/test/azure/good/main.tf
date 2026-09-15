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
