data "aws_iam_policy_document" "scoped_action" {
  statement {
    sid       = "Scoped"
    effect    = "Allow"
    actions   = ["s3:GetObject", "s3:ListBucket"]
    resources = ["arn:aws:s3:::example-bucket/*"]
  }
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

resource "aws_iam_role" "tagged" {
  name = "example-tagged-role"
  assume_role_policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Effect = "Allow", Action = "sts:AssumeRole", Principal = { Service = "ec2.amazonaws.com" } }]
  })

  tags = {
    Owner       = "platform-team"
    Environment = "dev"
  }
}

resource "aws_iam_role_policy_attachment" "scoped_attachment" {
  role       = aws_iam_role.tagged.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
}
