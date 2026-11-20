output "rds_host" {
  description = "RDS instance hostname"
  value       = aws_db_instance.postgres.address
}

output "rds_port" {
  description = "RDS instance port"
  value       = aws_db_instance.postgres.port
}

output "rds_endpoint" {
  description = "RDS instance endpoint (host:port)"
  value       = aws_db_instance.postgres.endpoint
}

output "database_url" {
  # The AWS emulator provides RDS API emulation only — it does not expose a
  # real PostgreSQL wire endpoint. Actual connections use the postgres:16
  # sidecar container on 127.0.0.1:5433 (managed by manage.sh emulator:start).
  description = "SQLAlchemy connection URL for the main database (postgres sidecar)"
  value       = "postgresql+psycopg2://${var.db_username}:${var.db_password}@127.0.0.1:5433/instructor_db"
  sensitive   = true
}

output "test_database_url" {
  description = "SQLAlchemy connection URL for the test database (postgres sidecar)"
  value       = "postgresql+psycopg2://${var.db_username}:${var.db_password}@127.0.0.1:5433/instructor_test_db"
  sensitive   = true
}

output "ecr_repository_url" {
  description = "ECR repository URL for the API image"
  value       = aws_ecr_repository.api.repository_url
}

output "alb_dns_name" {
  description = "ALB DNS name"
  value       = aws_lb.main.dns_name
}

output "api_url" {
  description = "Base URL for the API"
  value       = "http://${aws_lb.main.dns_name}"
}

output "frontend_bucket" {
  description = "S3 bucket name for the frontend"
  value       = aws_s3_bucket.frontend.id
}

output "cloudfront_domain" {
  description = "CloudFront distribution domain name"
  value       = aws_cloudfront_distribution.frontend.domain_name
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID"
  value       = aws_cloudfront_distribution.frontend.id
}
