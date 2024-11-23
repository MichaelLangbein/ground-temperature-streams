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

resource "null_resource" "package_function" {
  provisioner "local-exec" {
    command = "zip functionSource.zip main.py"
  }
  triggers = {
    # always_run = "${timestamp()}"
    file_hash_main = "${md5(file("./main.py"))}"
  }
}

resource "google_storage_bucket_object" "source_code" {
  name   = "functionSource.zip"
  bucket = google_storage_bucket.source_code_bucket_1234.name
  source = "./functionSource.zip"
  # to make sure that this updates when the zip file changes,
  # both `depends_on` and `lifecycle` are required!
  depends_on = [null_resource.package_function]
  lifecycle {
    create_before_destroy = true
  }
}

# resource "google_cloudfunctions_function" "check_data" {
#   name                  = "check_data"
#   runtime               = "python310"
#   entry_point           = "entryPoint"
#   source_archive_bucket = google_storage_bucket.source_code_bucket_1234.name
#   source_archive_object = google_storage_bucket_object.source_code.name
#   event_trigger {
#     event_type = "google.pubsub.topic.publish"
#     resource   = google_pubsub_topic.heartbeat_topic.id
#   }
#   available_memory_mb   = 256
# }

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
  }
  service_config {
    max_instance_count = 1
    available_memory   = "256M"
  }
  depends_on = [google_storage_bucket_object.source_code]
}