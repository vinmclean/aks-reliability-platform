output "vnet_id" {
  value = azurerm_virtual_network.vnet.id
}

output "services_subnet_id" {
  value = azurerm_subnet.services_subnet.id
}

output "aks_subnet_id" {
  value = azurerm_subnet.aks_subnet.id
}