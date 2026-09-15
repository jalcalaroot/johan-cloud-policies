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
