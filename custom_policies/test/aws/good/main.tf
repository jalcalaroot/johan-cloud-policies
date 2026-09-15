data "aws_iam_policy_document" "scoped_action" {
  statement {
    sid       = "Scoped"
    effect    = "Allow"
    actions   = ["s3:GetObject", "s3:ListBucket"]
    resources = ["arn:aws:s3:::example-bucket/*"]
  }
}

resource "aws_iam_role" "with_boundary" {
  name                 = "with-boundary-role"
  permissions_boundary = "arn:aws:iam::123456789012:policy/DeveloperBoundary"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

data "aws_iam_policy_document" "deny_wildcard_is_fine" {
  statement {
    sid       = "DenyOutsideRegion"
    effect    = "Deny"
    actions   = ["*"]
    resources = ["*"]
    condition {
      test     = "StringNotEquals"
      variable = "aws:RequestedRegion"
      values   = ["us-east-1"]
    }
  }
}
