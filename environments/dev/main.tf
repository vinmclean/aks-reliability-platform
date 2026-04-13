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

module "aks" {
  source = "../../modules/aks"

  environment  = "dev"
  cluster_name = "dev-aks"
  acr_id       = module.acr.acr_id
  subnet_id    = module.vnet.aks_subnet_id
}