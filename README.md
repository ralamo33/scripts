# Uses
* Load in a dataset from Hugging Face & upload the images to GCP. Then output a sql file taht would let you load these rows into a postgresql db.

# Install
To use first set your .env file with
1. HF_TOKEN where the value is a HuggingFace AccessToken
2. GOOGLE_PROJECT_ID the google project id
3. BUCKET_NAME the google cloud storage bucket name

Then use uv package manger for dependencies

### Other
Create a service-account.json file with the creds of a Google Service account with ability to read & write to GCP buckets
