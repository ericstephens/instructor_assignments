# NOTE: The AWS emulator accepts the RDS create-db-instance API call and
# returns a syntactically valid endpoint, but it does not start a real
# PostgreSQL process. Actual database connections use the postgres:16 sidecar
# container started by `manage.sh emulator:start` (127.0.0.1:5433).
# This resource models the production RDS configuration; in a real AWS
# environment it would provision the actual database.

resource "aws_db_subnet_group" "main" {
  name       = "${var.app_name}-db-subnet-group"
  subnet_ids = [aws_subnet.public_1.id, aws_subnet.public_2.id]

  tags = {
    Name = "${var.app_name}-db-subnet-group"
  }
}

resource "aws_db_instance" "postgres" {
  identifier        = "${var.app_name}-db"
  engine            = "postgres"
  engine_version    = "16"
  instance_class    = "db.t3.micro"
  allocated_storage = 20

  db_name  = "instructor_db"
  username = var.db_username
  password = var.db_password

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds_sg.id]

  publicly_accessible = true
  skip_final_snapshot = true
  apply_immediately   = true

  tags = {
    Name = "${var.app_name}-db"
  }
}
