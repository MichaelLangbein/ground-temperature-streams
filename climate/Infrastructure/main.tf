#-----------------------------------------------------------------
# providers
#-----------------------------------------------------------------

terraform {
  required_providers {
    google = {
      source = "hashicorp/google"
    }
    docker = {
      source = "kreuzwerker/docker"
    }
  }
}


provider "google" {
  project = var.project_id
  region  = var.region
}

provider "docker" {
  host = "unix:///var/run/docker.sock"
}

#-----------------------------------------------------------------
# data storage bucket
#-----------------------------------------------------------------

resource "google_storage_bucket" "data_bucket" {
  name     = "data_bucket"
  location = var.region
}


#-----------------------------------------------------------------
# pubsub
#-----------------------------------------------------------------

resource "google_project_service" "pubsub_api" {
  service                    = "pubsub.googleapis.com"
  project                    = var.project_id
  disable_dependent_services = true
}

resource "google_pubsub_topic" "download_request_topic" {
  name    = "download_request_topic"
  project = var.project_id
}

resource "google_pubsub_topic" "processing_request_topic" {
  name    = "processing_request_topic"
  project = var.project_id
}


#-----------------------------------------------------------------
# code to image repo
#-----------------------------------------------------------------


resource "google_artifact_registry_repository" "registry" {
  format        = "docker"
  repository_id = "climate_docker_images"
  location      = var.region
}

locals {
  downloader_source_files   = fileset("../Downloader/", "**/*.py")
  downloader_source_content = join("", [for file in local.downloader_source_files : file("./Downloader/${file}")])
  downloader_source_hash    = md5(local.downloader_source_content)
  downloader_image_name     = "europe-west3-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.registry.name}/downloader:${local.downloader_source_hash}"
}

resource "docker_image" "downloader_image" {
  name = local.downloader_image_name
  build {
    context = "./Downloader"
  }
  triggers = {
    source_hash = local.downloader_source_hash
    docker_hash = "${md5(file("./Downloader/Dockerfile"))}"
  }
}

# pushing image to gcp image repo. 
# weirdly, there is no idiomatic terraform resource to accomplish this.
resource "null_resource" "push_downloader_image" {
  provisioner "local-exec" {
    command = "docker push ${local.downloader_image_name}"
  }
  triggers = {
    image_id = docker_image.downloader_image.image_id
  }
  depends_on = [docker_image.downloader_image]
}


#-----------------------------------------------------------------
# cloud run instances
#-----------------------------------------------------------------

resource "google_project_service" "cloud_run_api" {
  service = "run.googleapis.com"
  project = var.project_id
}

resource "google_cloud_run_service" "downloader_service" {
  name     = "downloader_service"
  location = var.region
  template {
    spec {
      #   service_account_name = google_service_account.pubsub_cloudrun_sa.email
      containers {
        image = local.downloader_image_name
        env {
          name  = "target_topic"
          value = google_pubsub_topic.data_topic.id
        }
        env {
          name  = "usgs_username"
          value = var.usgs_username
        }
        env {
          name  = "usgs_password"
          value = var.usgs_password
        }
        env {
          name  = "target_bucket"
          value = google_storage_bucket.data_bucket.name
        }
      }
    }
    metadata {
      annotations = {
        "autoscaling.knative.dev/maxScale" : "1"
      }
    }
  }
  traffic {
    percent         = 100
    latest_revision = true
  }
  depends_on = [
    google_project_service.cloud_run_api,
    docker_image.downloader_image,
    null_resource.push_downloader_image
  ]
}


resource "google_pubsub_subscription" "push_to_downloader" {
  name  = "push-to-downloader"
  topic = google_pubsub_topic.download_request_topic.name
  push_config {
    # This has pubsub post it's messages to our cloudrun instance
    push_endpoint = "${google_cloud_run_service.downloader_service.status[0].url}/download"
    # giving the subscription the same user as the cloudrun instance
    # ... not sure if this is actually required
    # oidc_token {
    #   service_account_email = google_service_account.pubsub_cloudrun_sa.email
    # }
  }
}
