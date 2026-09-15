data "aws_iam_policy_document" "wildcard_action" {
  statement {
    sid       = "TooWide"
    effect    = "Allow"
    actions   = ["*"]
    resources = ["arn:aws:s3:::example-bucket/*"]
  }
}

resource "aws_iam_role" "untagged" {
  name = "example-untagged-role"
  assume_role_policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Effect = "Allow", Action = "sts:AssumeRole", Principal = { Service = "ec2.amazonaws.com" } }]
  })
}

resource "aws_iam_role_policy_attachment" "admin_attachment" {
  role       = aws_iam_role.untagged.name
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
}
