variable "project_id" {
  description = "The project ID for Google Cloud."
  type        = string
  default     = "deleteme-443412"
}

variable "region" {
  type    = string
  default = "europe-west3"
}

variable "usgs_username" {
  type = string
}

variable "usgs_password" {
  type = string
}