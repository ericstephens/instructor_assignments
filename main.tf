terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  # local backend (no S3 state for local dev)
}

provider "aws" {
  region = var.aws_region

  skip_metadata_api_check     = true
  skip_credentials_validation = true
  skip_requesting_account_id  = true
}

# AWS_ENDPOINT_URL, AWS_CA_BUNDLE, AWS_SHARED_CREDENTIALS_FILE are set via localENV
