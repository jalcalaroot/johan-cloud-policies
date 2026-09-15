data "aws_iam_policy_document" "wildcard_action" {
  statement {
    sid       = "TooWide"
    effect    = "Allow"
    actions   = ["*"]
    resources = ["arn:aws:s3:::example-bucket/*"]
  }
}
