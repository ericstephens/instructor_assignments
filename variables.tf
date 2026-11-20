variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "db_username" {
  description = "RDS master username"
  type        = string
  default     = "postgres"
}

variable "db_password" {
  description = "RDS master password"
  type        = string
  sensitive   = true
  default     = "instructor_pass_local"
}

variable "jwt_secret_key" {
  description = "JWT signing secret"
  type        = string
  sensitive   = true
  default     = "change-me-in-production"
}

variable "notify_from_email" {
  description = "From address used by the notification service"
  type        = string
  default     = "noreply@instructor-system.local"
}

variable "cors_origins" {
  description = "Comma-separated list of allowed CORS origins"
  type        = string
  default     = "http://localhost:5173,http://localhost:3000"
}

variable "app_name" {
  description = "Short application name used as a prefix for resource names"
  type        = string
  default     = "instructor"
}
