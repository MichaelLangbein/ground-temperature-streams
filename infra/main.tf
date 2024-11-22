provider "google" {
  project = var.project_id
  region  = var.region
}

#------------------------------------------------------------------------------------------------------------
# REQUIRED SERVICES / API's
#------------------------------------------------------------------------------------------------------------

resource "google_project_service" "cloud_scheduler_api" {
  service = "cloudscheduler.googleapis.com"
  project = var.project_id
}

resource "google_project_service" "cloud_functions_api" {
  service = "cloudfunctions.googleapis.com"
  project = var.project_id
}

resource "google_project_service" "artifact_registry_api" {
  service = "artifactregistry.googleapis.com"
  project = var.project_id
}

resource "google_project_service" "cloud_build_api" {
  service = "cloudbuild.googleapis.com"
  project = var.project_id
}

#------------------------------------------------------------------------------------------------------------
# INFRASTUCTURE
#------------------------------------------------------------------------------------------------------------


# pubsub
resource "google_pubsub_topic" "heartbeat_topic" {
  name = "heartbeat_topic"
}
resource "google_pubsub_subscription" "heartbeat_subscription" {
  name  = "heartbeat_subscription"
  topic = google_pubsub_topic.heartbeat_topic.name
}

# timer 
resource "google_cloud_scheduler_job" "clock" {
  name      = "clock"
  schedule  = "*/10 * * * *"
  time_zone = "UTC"
  pubsub_target {
    topic_name = google_pubsub_topic.heartbeat_topic.id
    attributes = {
      message = "tick tock"
    }
  }
}

# # output bucket
# resource "google_storage_bucket" "data_bucket" {
#   name     = "lst_data_bucket"
#   location = var.region
# }





# bucket for function-code
resource "google_storage_bucket" "source_code_bucket" {
  name     = "lst_source_code_bucket"
  location = var.region
}
# zipping function code for upload
resource "null_resource" "package_function" {
  provisioner "local-exec" {
    command = "cd ../WatchData && zip -r functionSource.zip ./*"
  }
  triggers = {
    file_hash = "${md5(file("../WatchData/main.py"))}"
  }
}
# function-code
resource "google_storage_bucket_object" "source_code" {
  name   = "source_code"
  bucket = google_storage_bucket.source_code_bucket.id
  source = "../WatchData/functionSource.zip"
}

# function 
resource "google_cloudfunctions_function" "watch_data" {
  name                  = "watch_data"
  runtime               = "python311"
  entry_point           = "scanForNewData"
  source_archive_bucket = google_storage_bucket.source_code_bucket.name
  source_archive_object = google_storage_bucket_object.source_code.name
  event_trigger {
    event_type = "google.pubsub.topic.publish"
    resource   = google_pubsub_topic.heartbeat_topic.id
  }
  available_memory_mb   = 256
  timeout               = 60
  environment_variables = {}
}

