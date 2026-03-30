module "vnet" {
  source = "../../modules/vnet"

  environment          = var.environment
  address_space        = var.address_space
  services_subnet_cidr = var.services_subnet_cidr
  aks_subnet_cidr      = var.aks_subnet_cidr
}

module "acr" {
  source = "../../modules/acr"

  environment = var.environment
}