data "azurerm_resource_group" "dev_rg" {
  name = "rg-aks-reliability-dev"
}

resource "azurerm_kubernetes_cluster" "aks" {
  name                              = var.cluster_name
  resource_group_name               = data.azurerm_resource_group.dev_rg.name
  location                          = data.azurerm_resource_group.dev_rg.location
  dns_prefix                        = "${var.cluster_name}-dns"
  role_based_access_control_enabled = true # enable RBAC 
  oidc_issuer_enabled               = true

  default_node_pool {
    name           = "system"
    node_count     = var.node_count
    vm_size        = var.vm_size
    vnet_subnet_id = var.subnet_id
  }

  identity {
    type = "SystemAssigned"
  }

  network_profile {
    network_plugin = "azure" # Azure CNI
  }

}

resource "azurerm_role_assignment" "acr_pull" {
  principal_id         = azurerm_kubernetes_cluster.aks.kubelet_identity[0].object_id
  scope                = var.acr_id
  role_definition_name = "AcrPull"
}