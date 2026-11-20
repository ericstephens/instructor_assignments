resource "aws_ecr_repository" "api" {
  name                 = "${var.app_name}-api"
  force_delete         = true
  image_tag_mutability = "MUTABLE"

  tags = {
    Name = "${var.app_name}-api"
  }
}
