provider "google" {
  project = var.project_id
  region = var.region
}


# pubsub
resource "google_pubsub_topic" "heartbeat_topic" {
  name = "heartbeat_topic"
}
resource "google_pubsub_subscription" "heartbeat_subscription" {
  name = "heartbeat_subscription"
  topic = google_pubsub_topic.heartbeat_topic.name
}

# timer 
resource "google_cloud_scheduler_job" "clock" {
  name = "clock"
  schedule = "*/10 * * * *"
  time_zone = "UTC"
  pubsub_target {
    topic_name = google_pubsub_topic.heartbeat_topic.id
    attributes = {
      message = "tick tock"
    }
  }
}

# output bucket
resource "google_storage_bucket" "data_bucket" {
  name = "data_bucket"
  location = var.region
}

# bucket for function-code
resource "google_storage_bucket" "source_code_bucket" {
  name = "source_code_bucket"
  location = var.region
}

# function-code
resource "google_storage_bucket_object" "source_code" {
  name = "source_code"
  bucket = google_storage_bucket.source_code_bucket.id
  source = "../downloader"
}

# function 
resource "google_cloudfunctions_function" "downloader" {
  name = "downloader"
  runtime = "python311"
  entry_point = "scanForNewData"
  source_archive_bucket = google_storage_bucket.source_code_bucket.id
  source_archive_object = google_storage_bucket_object.source_code.id
  event_trigger {
    event_type = "google.pubsub.topic.publish"
    resource = google_pubsub_topic.heartbeat_topic.id
  }
  available_memory_mb = 256
  timeout = 60
  environment_variables = {
    TARGET_BUCKET = google_storage_bucket.data_bucket.name
  }
}

