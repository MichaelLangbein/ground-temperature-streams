
variable "project_id" {
  description = "The project ID for Google Cloud."
  type        = string
  default     = "experiments-442613"
}

variable "region" {
  description = "Region"
  type        = string
  default     = "europe-west3"
}

variable "repo" {
  type    = string
  default = "https://github.com/MichaelLangbein/ground-temperature-streams"
}