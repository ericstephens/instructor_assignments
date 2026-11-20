resource "aws_ses_email_identity" "notify_from" {
  email = var.notify_from_email
}
