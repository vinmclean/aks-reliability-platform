data "azurerm_resource_group" "dev_rg" {
  name = "rg-aks-reliability-dev"
}

resource "azurerm_kubernetes_cluster" "aks" {
  name                = var.cluster_name
  resource_group_name = data.azurerm_resource_group.dev_rg.name
  location            = data.azurerm_resource_group.dev_rg.location
  dns_prefix          = "${var.cluster_name}-dns"

  default_node_pool {
    name       = "system"
    node_count = var.node_count
    vm_size    = var.vm_size
  }

  identity {
    type = "SystemAssigned"
  }

}