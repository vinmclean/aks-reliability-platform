variable "acr_id" {
  description = "Azure container registery id to connect AKS cluster"
}

variable "cluster_name" {
  description = "Name of the AKS cluster"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, prod)"
  type        = string
}

variable "node_count" {
  default = 2
  type    = number
}

variable "services_subnet_id" {
  description = "Subnet for k8 default cluster"
  type        = string
}

variable "app_subnet_id" {
  description = "Subnet for aks (app workload) cluster"
  type        = string
}

variable "vm_size" {
  description = "VM size for AKS nodes"
  default     = "Standard_B2s"
  type        = string
}