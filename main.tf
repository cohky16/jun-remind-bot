terraform {
  required_providers {
    mongodbatlas = {
      source = "mongodb/mongodbatlas"
      version = "1.4.2"
    }
    aws = {
      source = "hashicorp/aws"
      version = "4.22.0"
    }
  }
}

provider "mongodbatlas" {}

variable "MONGODB_ORG_ID" {} 
variable "MONGODB_API_KEY" {} 

resource "mongodbatlas_project" "jrb" {
  name   = "jrb"
  org_id = var.MONGODB_ORG_ID

  api_keys {
    api_key_id = var.MONGODB_API_KEY
    role_names = [
      "GROUP_OWNER",
    ]
  }

  is_collect_database_specifics_statistics_enabled = true
  is_data_explorer_enabled                         = true
  is_performance_advisor_enabled                   = true
  is_realtime_performance_panel_enabled            = true
  is_schema_advisor_enabled                        = true
}

resource "mongodbatlas_cluster" "jrb" {
    name = "jrb"
    project_id = mongodbatlas_project.jrb.id
    provider_instance_size_name = "M0"
    provider_name = "TENANT"
    auto_scaling_compute_enabled = false
    auto_scaling_compute_scale_down_enabled = false
    auto_scaling_disk_gb_enabled = null
    backing_provider_name = "AWS"
    cloud_backup = false
    cluster_type = "REPLICASET"
    disk_size_gb = 0.5
    encryption_at_rest_provider = "NONE"
    mongo_db_major_version = "5.0"
    pit_enabled = false
    provider_region_name = "AP_NORTHEAST_1"
    replication_factor = 3
    replication_specs {
        regions_config {
            analytics_nodes = 0
            electable_nodes = 3
            priority        = 7
            read_only_nodes = 0
            region_name     = "AP_NORTHEAST_1"
        }
        num_shards = 1
        zone_name = "Zone 1"
    }
}

variable "AWS_ACCESS_KEY_ID" {}
variable "AWS_SECRET_ACCESS_KEY" {}
variable "AWS_REGION" {}

provider "aws" {
  access_key = var.AWS_ACCESS_KEY_ID
  secret_key = var.AWS_SECRET_ACCESS_KEY
  region     = var.AWS_REGION
}

resource "aws_iam_role" "sts_for_iam" {
  name = "sts_for_iam"
  assume_role_policy = <<-EOF
  {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Action": "sts:AssumeRole",
        "Principal": {
          "Service": "lambda.amazonaws.com"
        },
        "Effect": "Allow",
        "Sid": ""
      }
    ]
  }
  EOF
}

data "aws_caller_identity" "current" {}

resource "aws_iam_role_policy" "iam_for_lambda" {
  name = "iam_for_lambda"
  role = aws_iam_role.sts_for_iam.id
  policy = <<-EOF
  {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "logs:CreateLogGroup",
            "Resource": "arn:aws:logs:ap-northeast-1:${data.aws_caller_identity.current.account_id}:*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": [
                "arn:aws:logs:ap-northeast-1:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/batch_jun_remind:*"
            ]
        }
    ]
  }
  EOF
}

data "archive_file" "go" {
  type        = "zip"
  source_file = "jrb"
  output_path = "upload.zip"
}

variable "APP_ENV" {} 
variable "CLIENT_ID" {} 
variable "CLIENT_SECRET" {} 
variable "LINE_CHANNEL_ACCESS_TOKEN" {} 
variable "LINE_CHANNEL_SECRET" {} 
variable "MONGODB_URI" {} 

resource "aws_lambda_function" "batch_jun_remind" {
  filename      = "upload.zip"
  function_name = "batch_jun_remind"
  role          = aws_iam_role.sts_for_iam.arn
  handler       = "jrb"
  architectures = ["x86_64"]
  runtime = "go1.x"
  timeout = 180

  environment {
    variables = {
      APP_ENV = var.APP_ENV
      CLIENT_ID = var.CLIENT_ID
      CLIENT_SECRET = var.CLIENT_SECRET
      LINE_CHANNEL_ACCESS_TOKEN = var.LINE_CHANNEL_ACCESS_TOKEN
      LINE_CHANNEL_SECRET = var.LINE_CHANNEL_SECRET
      MONGODB_URI = var.MONGODB_URI
    }
  }
}

resource "aws_cloudwatch_log_group" "log" {
  name              = "/aws/lambda/${aws_lambda_function.batch_jun_remind.function_name}"
  retention_in_days = 14
}

resource "aws_cloudwatch_event_rule" "every_minutes" {
    name                = "every_minutes"
    description         = "every_minutes"
    schedule_expression = "rate(1 minute)"
}

resource "aws_cloudwatch_event_target" "target" {
    target_id = "batch_jun_remind"
    rule      = aws_cloudwatch_event_rule.every_minutes.name
    arn       = aws_lambda_function.batch_jun_remind.arn
}

resource "aws_lambda_permission" "permission" {
    statement_id  = "AllowExecutionFromCloudWatch"
    action        = "lambda:InvokeFunction"
    function_name = aws_lambda_function.batch_jun_remind.function_name
    principal     = "events.amazonaws.com"
    source_arn    = aws_cloudwatch_event_rule.every_minutes.arn
}