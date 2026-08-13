data "azurerm_resource_group" "dev_rg" {
  name = "rg-aks-reliability-dev"
}

resource "azurerm_container_registry" "acr" {
  name                = "${var.environment}ACR674"
  resource_group_name = data.azurerm_resource_group.dev_rg.name
  location            = data.azurerm_resource_group.dev_rg.location
  sku                 = "Basic"
}

resource "azurerm_role_assignment" "acr_push" {
  principal_id         = var.service_principal_id
  scope                = azurerm_container_registry.acr.id
  role_definition_name = "AcrPush"
}