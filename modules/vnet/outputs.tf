output "vnet_id" {
  value = azurerm_virtual_network.vnet.id
}

output "system_node_subnet_id" {
  value = azurerm_subnet.system_node_subnet.id
}

output "app_node_subnet_id" {
  value = azurerm_subnet.app_node_subnet.id
}