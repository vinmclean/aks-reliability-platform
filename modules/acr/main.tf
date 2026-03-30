data "azurerm_resource_group" "dev_rg" {
  name = "rg-aks-reliability-dev"
}

resource "azurerm_container_registry" "acr" {
  name                = "${var.environment}ACR674"
  resource_group_name = data.azurerm_resource_group.dev_rg.name
  location            = data.azurerm_resource_group.dev_rg.location
  sku                 = "Basic"
}