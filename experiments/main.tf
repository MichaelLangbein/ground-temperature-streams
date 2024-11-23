provider "google" {
  project     = var.project_id
  region      = var.region
  credentials = file("./mykeyfile.json")
}

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

resource "google_storage_bucket" "source_code_bucket_1234" {
  name     = "source_code_bucket_1234"
  location = var.region
}

data "archive_file" "source_code" {
  type        = "zip"
  source_dir  = "./src/"
  output_path = "./functionSource.zip"
}

# Updating name ensures that the source code is re-uploaded
# https://stackoverflow.com/questions/71320503/is-it-possible-to-update-the-source-code-of-a-gcp-cloud-function-in-terraform
resource "google_storage_bucket_object" "source_code" {
  name   = "functionSource.${data.archive_file.source_code.output_md5}.zip"
  source = data.archive_file.source_code.output_path
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
        object = google_storage_bucket_object.source_code.name
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
  depends_on = [google_storage_bucket_object.source_code]
}