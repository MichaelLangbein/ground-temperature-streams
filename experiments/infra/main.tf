provider "google" {
  project     = var.project_id
  region      = var.region
  credentials = file("./mykeyfile.json")
}


#------------------------------------------------------------------------------------------------------------
# Pub/Sub, Scheduler
#------------------------------------------------------------------------------------------------------------

resource "google_pubsub_topic" "heartbeat_topic" {
  name = "heartbeat_topic"
}

resource "google_cloud_scheduler_job" "clock" {
  name      = "clock"
  schedule  = "* * * * *"
  time_zone = "Europe/Berlin"
  pubsub_target {
    topic_name = google_pubsub_topic.heartbeat_topic.id
    attributes = {
      message = "tick tock"
    }
  }
}



#------------------------------------------------------------------------------------------------------------
# Source code bucket
#------------------------------------------------------------------------------------------------------------

resource "google_storage_bucket" "source_code_bucket_1234" {
  name     = "source_code_bucket_1234"
  location = var.region
}



#------------------------------------------------------------------------------------------------------------
# Function
#------------------------------------------------------------------------------------------------------------

data "archive_file" "function_source_zip" {
  type        = "zip"
  source_dir  = "../WatchData/"
  output_path = "../FunctionSource.zip"
}

# Updating name ensures that the source code is re-uploaded
# https://stackoverflow.com/questions/71320503/is-it-possible-to-update-the-source-code-of-a-gcp-cloud-function-in-terraform
resource "google_storage_bucket_object" "function_source_code" {
  name   = "FunctionSource.${data.archive_file.function_source_zip.output_md5}.zip"
  source = data.archive_file.function_source_zip.output_path
  bucket = google_storage_bucket.source_code_bucket_1234.name
}

resource "google_cloudfunctions2_function" "check_data" {
  name        = "check_data"
  location    = var.region
  description = "Check if there is new data available"
  build_config {
    runtime     = "python310"
    entry_point = "entryPoint"
    source {
      storage_source {
        bucket = google_storage_bucket.source_code_bucket_1234.name
        object = google_storage_bucket_object.function_source_code.name
      }
    }
  }
  event_trigger {
    trigger_region = var.region
    event_type     = "google.cloud.pubsub.topic.v1.messagePublished"
    pubsub_topic   = google_pubsub_topic.heartbeat_topic.id
    retry_policy   = "RETRY_POLICY_DO_NOT_RETRY"
  }
  service_config {
    max_instance_count = 1
    available_memory   = "256M"
  }
  depends_on = [google_storage_bucket_object.function_source_code]
}



#------------------------------------------------------------------------------------------------------------
# Cloud Run
#------------------------------------------------------------------------------------------------------------



resource "google_artifact_registry_repository" "registry" {
  format        = "docker"
  repository_id = "mydockerimages"
  location      = var.region
}

# cd ../ProcessData/
# docker image build -t docker push europe-west3-docker.pkg.dev/experiments-442613/mydockerimages/processdata .
# docker push europe-west3-docker.pkg.dev/experiments-442613/mydockerimages/processdata


# resource "google_cloudbuild_trigger" "trigger" {
#   name        = "ProcessData trigger"
#   description = "Trigger to build container on push to master"
#   trigger_template {
#     repo_name   = var.repo
#     branch_name = "master"
#   }
#   github {
#     owner = "michaellangbein"
#     name  = "ground-temperature-streams"
#     push {
#       branch = "master"
#     }
#   }
#   build {
#     step {
#       name = "gcr.io/cloud-builders/docker"
#       args = ["build", "-t", "gcr.io/${var.project_id}/processdata:latest", "."]
#     }
#     images = ["gcr.io/${var.project_id}/processdata:latest"]
#   }
# }




resource "google_cloud_run_service" "process_data_service" {
  name     = "process-data-service"
  location = var.region
  template {
    spec {
      containers {
        image = "gcr.io/${var.project_id}/mydockerimages/processdata"
      }
    }
  }
  traffic {
    percent         = 100
    latest_revision = true
  }
}