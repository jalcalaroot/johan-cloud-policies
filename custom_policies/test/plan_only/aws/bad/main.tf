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
    sid     = "WildcardPrincipal"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "AWS"
      identifiers = ["*"]
    }
  }
}

resource "aws_iam_role" "test" {
  name               = "example-role"
  assume_role_policy = data.aws_iam_policy_document.assume.json
}

data "aws_iam_policy_document" "perms" {
  statement {
    sid       = "WildcardAction"
    actions   = ["s3:*"]
    resources = ["*"]
  }

  statement {
    sid       = "PassRoleWildcardUnconditioned"
    actions   = ["iam:PassRole"]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "test" {
  name   = "example-role-policy"
  role   = aws_iam_role.test.id
  policy = data.aws_iam_policy_document.perms.json
}
