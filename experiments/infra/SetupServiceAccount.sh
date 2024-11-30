#! /bin/bash


# create project
gcloud projects create experiments-442613
gcloud config set project experiments-442613
# @TODO: connect a billing-account/credit-card
echo "Don't forget to connect a billing-account/credit-card"

# create user
cloud iam service-accounts create trfmbot --display-name="terraform bot"
gcloud iam service-accounts keys create mykeyfile.json --iam-account=trfmbot@experiments-442613.iam.gserviceaccount.com

# Add permissions to your service-account as required by your main.tf.
# If you need a certain permission, find the matching role here:
# https://cloud.google.com/iam/docs/permissions-reference
# Also, find terrform documentation for different resources here:
# https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/

# activate pubsub api
gcloud services enable pubsub.googleapis.com
gcloud projects add-iam-policy-binding experiments-442613 --member="serviceAccount:trfmbot@experiments-442613.iam.gserviceaccount.com" --role="roles/pubsub.editor"

# activate storage api
gcloud services enable storage.googleapis.com
gcloud projects add-iam-policy-binding experiments-442613 --member="serviceAccount:trfmbot@experiments-442613.iam.gserviceaccount.com" --role="roles/storage.admin"

# activate cloud scheduler api
gcloud services enable cloudscheduler.googleapis.com
gcloud projects add-iam-policy-binding experiments-442613 --member="serviceAccount:trfmbot@experiments-442613.iam.gserviceaccount.com" --role="roles/cloudscheduler.admin"

# activate cloudfunctions api
gcloud services enable cloudfunctions.googleapis.com
# follow-up permissions associated with cloudfunctions:
gcloud services enable cloudbuild.googleapis.com
# The following permissions/roles are only required for cloudfunctions-version-1:
# gcloud iam service-accounts add-iam-policy-binding experiments-442613@appspot.gserviceaccount.com --member="serviceAccount:trfmbot@experiments-442613.iam.gserviceaccount.com" --role="roles/iam.serviceAccountUser"
# The following permissions/roles are only required for cloudfunctions-version-2:
gcloud projects add-iam-policy-binding experiments-442613 --member="serviceAccount:trfmbot@experiments-442613.iam.gserviceaccount.com" --role="roles/cloudfunctions.developer"
gcloud iam service-accounts add-iam-policy-binding projects/-/serviceAccounts/152847464795-compute@developer.gserviceaccount.com --member="serviceAccount:trfmbot@experiments-442613.iam.gserviceaccount.com" --role="roles/iam.serviceAccountUser"
gcloud services enable eventarc.googleapis.com
gcloud services enable run.googleapis.com

# activate artifact registry api
gcloud services enable artifactregistry.googleapis.com
gcloud projects add-iam-policy-binding experiments-442613 --member="serviceAccount:trfmbot@experiments-442613.iam.gserviceaccount.com" --role="roles/artifactregistry.admin"
gcloud projects add-iam-policy-binding experiments-442613 --member="serviceAccount:trfmbot@experiments-442613.iam.gserviceaccount.com" --role="roles/artifactregistry.createOnPushWriter"
# activate api's and permissions for github-build-trigger
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud projects add-iam-policy-binding experiments-442613 --member="serviceAccount:trfmbot@experiments-442613.iam.gserviceaccount.com" --role="roles/storage.admin"

# allow cloud run
gcloud projects add-iam-policy-binding experiments-442613 --member="serviceAccount:trfmbot@experiments-442613.iam.gserviceaccount.com" --role="roles/run.admin"

# sleep for one minute to allow permissions to propagate
sleep 60