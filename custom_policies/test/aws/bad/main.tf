data "aws_iam_policy_document" "wildcard_action" {
  statement {
    sid       = "TooWide"
    effect    = "Allow"
    actions   = ["*"]
    resources = ["arn:aws:s3:::example-bucket/*"]
  }
}

resource "aws_iam_role" "no_boundary" {
  name = "no-boundary-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}
