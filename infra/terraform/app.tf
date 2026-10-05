# ---------- Container registry ----------
resource "aws_ecr_repository" "app" {
  name                 = local.name
  image_tag_mutability = "MUTABLE"
  force_delete         = true
  image_scanning_configuration { scan_on_push = true }
  tags = local.tags
}

# ---------- Networking: App Runner -> RDS via VPC connector ----------
resource "aws_security_group" "apprunner" {
  name   = "${local.name}-apprunner"
  vpc_id = data.aws_vpc.default.id
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  tags = local.tags
}

resource "aws_apprunner_vpc_connector" "this" {
  vpc_connector_name = "${local.name}-vpc"
  subnets            = data.aws_subnets.default.ids
  security_groups    = [aws_security_group.apprunner.id]
  tags               = local.tags
}

# ---------- IAM ----------
data "aws_iam_policy_document" "build_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["build.apprunner.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ecr_access" {
  name               = "${local.name}-ecr-access"
  assume_role_policy = data.aws_iam_policy_document.build_assume.json
}

resource "aws_iam_role_policy_attachment" "ecr_access" {
  role       = aws_iam_role.ecr_access.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess"
}

data "aws_iam_policy_document" "task_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["tasks.apprunner.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "instance" {
  name               = "${local.name}-instance"
  assume_role_policy = data.aws_iam_policy_document.task_assume.json
}

data "aws_iam_policy_document" "read_secret" {
  statement {
    actions   = ["secretsmanager:GetSecretValue"]
    resources = [aws_secretsmanager_secret.db_url.arn]
  }
}

resource "aws_iam_role_policy" "read_secret" {
  role   = aws_iam_role.instance.id
  policy = data.aws_iam_policy_document.read_secret.json
}

# ---------- App Runner service ----------
resource "aws_apprunner_service" "app" {
  service_name = local.name

  source_configuration {
    auto_deployments_enabled = true
    authentication_configuration { access_role_arn = aws_iam_role.ecr_access.arn }
    image_repository {
      image_repository_type = "ECR"
      image_identifier      = "${aws_ecr_repository.app.repository_url}:${var.image_tag}"
      image_configuration {
        port                          = "8000"
        runtime_environment_variables = var.app_env
        runtime_environment_secrets   = { DATABASE_URL = aws_secretsmanager_secret.db_url.arn }
      }
    }
  }

  instance_configuration {
    cpu               = "0.25 vCPU"
    memory            = "0.5 GB"
    instance_role_arn = aws_iam_role.instance.arn
  }

  network_configuration {
    egress_configuration {
      egress_type       = "VPC"
      vpc_connector_arn = aws_apprunner_vpc_connector.this.arn
    }
  }

  health_check_configuration {
    protocol = "HTTP"
    path     = "/health"
  }

  tags       = local.tags
  depends_on = [aws_iam_role_policy_attachment.ecr_access]
}
