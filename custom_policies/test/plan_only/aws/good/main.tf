terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.64"
    }
  }
}

provider "aws" {
  region                      = "us-east-1"
  access_key                  = "test"
  secret_key                  = "test"
  skip_credentials_validation = true
  skip_requesting_account_id  = true
  skip_metadata_api_check     = true
}

data "aws_iam_policy_document" "assume" {
  statement {
    sid     = "ScopedPrincipal"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "test" {
  name               = "example-role"
  assume_role_policy = data.aws_iam_policy_document.assume.json
}

data "aws_iam_policy_document" "perms" {
  statement {
    sid       = "ScopedAction"
    actions   = ["s3:GetObject"]
    resources = ["arn:aws:s3:::example-bucket/*"]
  }

  statement {
    sid       = "PassRoleWithCondition"
    actions   = ["iam:PassRole"]
    resources = ["*"]
    condition {
      test     = "StringEquals"
      variable = "iam:PassedToService"
      values   = ["vpc-flow-logs.amazonaws.com"]
    }
  }
}

resource "aws_iam_role_policy" "test" {
  name   = "example-role-policy"
  role   = aws_iam_role.test.id
  policy = data.aws_iam_policy_document.perms.json
}
