variable "project_id" {
  description = "The project ID for Google Cloud."
  type        = string
}

variable "region" {
  description = "The region where resources will be deployed."
  type        = string
  default     = "europe-west1"
}