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

resource "google_storage_bucket" "data_bucket_climate123" {
  name          = "data_bucket_climate123"
  location      = var.region
  force_destroy = true
}


#-----------------------------------------------------------------
# pubsub
#-----------------------------------------------------------------

resource "google_service_account" "pubsub_sa" {
  account_id   = "pubsub-sa"
  display_name = "Pub/Sub SA that can invoke Cloud Run"
}

resource "google_project_iam_binding" "cloudrun_invoking" {
  project = var.project_id
  role    = "roles/run.invoker"
  members = ["serviceAccount:${google_service_account.pubsub_sa.email}", ]
}

resource "google_project_service" "pubsub_api" {
  service                    = "pubsub.googleapis.com"
  project                    = var.project_id
  disable_dependent_services = true
}

resource "google_pubsub_schema" "download_request_schema" {
  name       = "download_request_schema"
  type       = "AVRO"
  definition = <<AVRO
    {
      "type": "record",
      "name": "download_request",
      "fields": [
        {"name": "startDate", "type": "string", "doc": "YYYY-MM-DD"},
        {"name": "endDate", "type": "string", "doc": "YYYY-MM-DD"},
        {"name": "latMin", "type": "float"},
        {"name": "lonMin", "type": "float"},
        {"name": "latMax", "type": "float"},
        {"name": "lonMax", "type": "float"}
      ]
    }
  AVRO
}

resource "google_pubsub_schema" "processing_request_schema" {
  name       = "processing_request_schema"
  type       = "AVRO"
  definition = <<AVRO
    {
      "type": "record",
      "name": "processing_request",
      "fields": [
        {"name": "bucketName", "type": "string", "doc": "bucket name"}
        {"name": "blobName", "type": "string", "doc": "blob name"}
      ]
    }
  AVRO
}

resource "google_pubsub_topic" "download_request_topic" {
  name    = "download_request_topic"
  project = var.project_id
  schema_settings {
    schema   = google_pubsub_schema.download_request_schema.id
    encoding = "JSON"
  }
}

resource "google_pubsub_topic" "processing_request_topic" {
  name    = "processing_request_topic"
  project = var.project_id
  schema_settings {
    schema   = google_pubsub_schema.processing_request_schema.id
    encoding = "JSON"
  }
}


#-----------------------------------------------------------------
# code to image repo (poor man's CI/CD)
#-----------------------------------------------------------------

resource "google_project_service" "registry_api" {
  service                    = "artifactregistry.googleapis.com"
  project                    = var.project_id
  disable_dependent_services = true
}

resource "google_artifact_registry_repository" "registry" {
  format        = "docker"
  repository_id = "climate-docker-images"
  location      = var.region
  depends_on    = [google_project_service.registry_api]
}

locals {
  downloader_source_files   = fileset("../Downloader/", "**/*.py")
  downloader_source_content = join("", [for file in local.downloader_source_files : file("../Downloader/${file}")])
  downloader_source_hash    = md5(local.downloader_source_content)
  downloader_image_name     = "europe-west3-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.registry.name}/downloader:${local.downloader_source_hash}"

  assimilator_source_files   = fileset("../Assimilator/", "**/*.py")
  assimilator_source_content = join("", [for file in local.assimilator_source_files : file("../Assimilator/${file}")])
  assimilator_source_hash    = md5(local.assimilator_source_content)
  assimilator_image_name     = "europe-west3-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.registry.name}/assimilator:${local.assimilator_source_hash}"
}

resource "docker_image" "downloader_image" {
  name = local.downloader_image_name
  build {
    context = "../Downloader"
  }
  triggers = {
    source_hash = local.downloader_source_hash
    docker_hash = "${md5(file("../Downloader/Dockerfile"))}"
  }
}

resource "docker_image" "assimilator_image" {
  name = local.assimilator_image_name
  build {
    context = "../Assimilator"
  }
  triggers = {
    source_hash = local.assimilator_source_hash
    docker_hash = "${md5(file("../Assimilator/Dockerfile"))}"
  }
}

# Pushing images to gcp image repo. 
# Weirdly, there is no idiomatic terraform resource to accomplish this.
# To be allowed to do this:
# gcloud auth configure-docker
# gcloud projects add-iam-policy-binding climate-443420 \
# --member=user:info@codeandcolors.net \
# --role=roles/artifactregistry.writer

resource "null_resource" "push_downloader_image" {
  provisioner "local-exec" {
    command = "docker push ${local.downloader_image_name}"
  }
  triggers = {
    image_id = docker_image.downloader_image.image_id
  }
  depends_on = [docker_image.downloader_image]

}

resource "null_resource" "push_assimilator_image" {
  provisioner "local-exec" {
    command = "docker push ${local.assimilator_image_name}"
  }
  triggers = {
    image_id = docker_image.assimilator_image.image_id
  }
  depends_on = [docker_image.assimilator_image]
}


#-----------------------------------------------------------------
# cloud run instances
#-----------------------------------------------------------------

resource "google_project_service" "cloud_run_api" {
  service = "run.googleapis.com"
  project = var.project_id
}

resource "google_cloud_run_service" "downloader_service" {
  name     = "downloader-service"
  location = var.region
  template {
    spec {
      containers {
        image = local.downloader_image_name
        env {
          name  = "target_topic"
          value = google_pubsub_topic.processing_request_topic.id
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
          value = google_storage_bucket.data_bucket_climate123.name
        }
        # requires a lot of memory for geotiffs
        resources {
          limits = {
            # "cpu"    = "1000m"
            "memory" = "4Gi"
          }
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
    # ensuring that this subscription can invoke cloudrun
    oidc_token {
      service_account_email = google_service_account.pubsub_sa.email
    }
  }

  # Set the retry policy: never retry isn't possible, 
  # the minimum is 5 retries
  retry_policy {
    # allowing lots of time for locks to be released
    minimum_backoff = "400s"
    maximum_backoff = "600s"
  }
}

#-----------------------------------------------------------------
# bigquery
#-----------------------------------------------------------------

resource "google_bigquery_dataset" "lst_dataset" {
  dataset_id = "lst_dataset"
  location   = "EU"
}

resource "google_bigquery_table" "lst_table" {
  dataset_id          = google_bigquery_dataset.lst_dataset.dataset_id
  table_id            = "lst_table"
  schema              = <<EOF
    [ 
      { "name": "longitude", "type": "FLOAT", "mode": "REQUIRED" }, 
      { "name": "latitude", "type": "FLOAT", "mode": "REQUIRED" }, 
      { "name": "h3index", "type": "STRING", "mode": "REQUIRED" }, 
      { "name": "date", "type": "DATE", "mode": "REQUIRED" }, 
      { "name": "landSurfaceTemperature", "type": "FLOAT", "mode": "NULLABLE" } 
    ] 
  EOF
  deletion_protection = false
}