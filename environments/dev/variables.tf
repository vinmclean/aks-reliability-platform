# variable "address_space" {
#   description = "CIDR range for the VNet"
#   type        = list(string)

# }

# variable "aks_subnet_cidr" {
#   description = "CIDR block for aks subnet"
#   type        = list(string)

# }

variable "environment" {
  description = "Environment name (dev, prod)"
  type        = string
}

# variable "services_subnet_cidr" {
#   description = "CIDR block for services subnet"
#   type        = list(string)

# }

variable "service_principal_id" {
  description = "service principal objectId for acrPush role assignment"
  type        = string
}
