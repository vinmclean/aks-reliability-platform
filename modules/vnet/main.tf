
data "azurerm_resource_group" "dev_rg" {
  name = "rg-aks-reliability-dev"
}

resource "azurerm_virtual_network" "vnet" {
  name                = "${var.environment}-vnet"
  location            = data.azurerm_resource_group.dev_rg.location
  resource_group_name = data.azurerm_resource_group.dev_rg.name
  address_space       = var.address_space

}

resource "azurerm_subnet" "services_subnet" {
  name                 = "${var.environment}-services-subnet"
  resource_group_name  = data.azurerm_resource_group.dev_rg.name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = var.services_subnet_cidr
}

resource "azurerm_subnet" "aks_subnet" {
  name                 = "${var.environment}-aks-subnet"
  resource_group_name  = data.azurerm_resource_group.dev_rg.name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = var.aks_subnet_cidr
}