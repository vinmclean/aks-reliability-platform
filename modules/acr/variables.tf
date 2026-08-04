variable "environment" {
  description = "Environment name (dev, prod)"
  type        = string
}

variable "service_principal_id" {
  description = "service principal objectId for acrPush role assignment"
  type = string
}