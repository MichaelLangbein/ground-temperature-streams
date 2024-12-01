terraform {
  required_providers {
    docker = {
      source = "kreuzwerker/docker"
    }
    google = {
      source = "hashicorp/google"
    }
  }
}

provider "docker" {
  host = "unix:///var/run/docker.sock"
}

provider "google" {
  project = var.project_id
  region  = var.region
}

#------------------------------------------------------------------------------------------------------------
# Service account
#------------------------------------------------------------------------------------------------------------

resource "google_service_account" "pubsub_cloudrun_sa" {
  account_id   = "pubsub-cloudrun-sa"
  display_name = "Pub/Sub and Cloud Run Service Account"
}

resource "google_project_iam_binding" "cloudrun_invoking" {
  project = var.project_id
  role    = "roles/run.invoker"
  members = ["serviceAccount:${google_service_account.pubsub_cloudrun_sa.email}", ]
}

#------------------------------------------------------------------------------------------------------------
# Pubsub & scheduler
#------------------------------------------------------------------------------------------------------------


resource "google_project_service" "cloud_scheduler_api" {
  service = "cloudscheduler.googleapis.com"
  project = var.project_id
}

resource "google_project_service" "pubsub_api" {
  service                    = "pubsub.googleapis.com"
  project                    = var.project_id
  disable_dependent_services = true
}

resource "google_pubsub_topic" "heartbeat_topic" {
  name    = "heartbeat_topic"
  project = var.project_id
}

resource "google_cloud_scheduler_job" "clock" {
  name      = "clock"
  schedule  = "* * * * *"
  time_zone = "Europe/Berlin"
  pubsub_target {
    topic_name = google_pubsub_topic.heartbeat_topic.id
    data       = base64encode("{ \"body\": \"tick tock\" }")
  }
  # NB: a scheduler can also use a HTTP_target to directly post to a service,
  # circumventing a pubsub queue.
  #   http_target {
  #     http_method = "POST"
  #     uri         = "https://example.com/"
  #     body        = base64encode("{\"foo\":\"bar\"}")
  #     headers = {
  #       "Content-Type" = "application/json"
  #     }
  #   }
  depends_on = [
    google_project_service.cloud_scheduler_api,
    google_project_service.pubsub_api
  ]
}


#------------------------------------------------------------------------------------------------------------
# Code to image repo
#------------------------------------------------------------------------------------------------------------

resource "google_artifact_registry_repository" "registry" {
  format        = "docker"
  repository_id = "mydockerimages"
  location      = var.region
}

locals {
  processor_source_files   = fileset("./processor", "**/*.py")
  processor_source_content = join("", [for file in local.processor_source_files : file("./processor/${file}")])
  processor_source_hash    = md5(local.processor_source_content)
  processor_image_name     = "europe-west3-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.registry.name}/processor:${local.processor_source_hash}"
}

resource "docker_image" "processor_image" {
  name = local.processor_image_name
  build {
    context = "./processor"
  }
  triggers = {
    source_hash = local.processor_source_hash
    docker_hash = "${md5(file("./processor/Dockerfile"))}"
  }
}


# pushing image to gcp image repo. 
# weirdly, there is no idiomatic terraform resource to accomplish this.
resource "null_resource" "push_docker_image" {
  provisioner "local-exec" {
    command = "docker push ${local.processor_image_name}"
  }
  triggers = {
    image_id = docker_image.processor_image.image_id
  }
  depends_on = [docker_image.processor_image]
}



#------------------------------------------------------------------------------------------------------------
# Cloud run instance
#------------------------------------------------------------------------------------------------------------

resource "google_project_service" "cloud_run_api" {
  service = "run.googleapis.com"
  project = var.project_id
}

resource "google_cloud_run_service" "processor_service" {
  name     = "process-data-service"
  location = var.region
  template {
    spec {
      service_account_name = google_service_account.pubsub_cloudrun_sa.email
      containers {
        image = local.processor_image_name
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
    docker_image.processor_image,
    null_resource.push_docker_image
  ]
}

resource "google_pubsub_subscription" "push_to_cloudrun" {
  name  = "push-to-cloudrun"
  topic = google_pubsub_topic.heartbeat_topic.name
  push_config {
    # This has pubsub post it's messages to our cloudrun instance
    push_endpoint = "${google_cloud_run_service.processor_service.status[0].url}/echo"
    # giving the subscription the same user as the cloudrun instance
    # ... not sure if this is actually required
    oidc_token {
      service_account_email = google_service_account.pubsub_cloudrun_sa.email
    }
  }
}