variable "address_space" {
  description = "CIDR range for the VNet"
  type        = list(string)
  default     = ["10.0.0.0/16"]
}

variable "aks_subnet_cidr" {
  description = "CIDR block for aks subnet"
  type        = list(string)
  default     = ["10.0.1.0/24"]
}

variable "environment" {
  description = "Environment name (dev, prod)"
  type        = string
}

variable "services_subnet_cidr" {
  description = "CIDR block for services subnet"
  type        = list(string)
  default     = ["10.0.2.0/24"]
}