# ---------- Custom domain (optional) ----------
# Buy the domain in Route 53 first (console > Route 53 > Registered domains).
# That auto-creates the hosted zone looked up below.
locals {
  use_domain = var.domain_name != ""
  hostname   = local.use_domain ? "${var.subdomain}.${var.domain_name}" : ""
}

data "aws_route53_zone" "this" {
  count = local.use_domain ? 1 : 0
  name  = var.domain_name
}

resource "aws_apprunner_custom_domain_association" "this" {
  count                = local.use_domain ? 1 : 0
  service_arn          = aws_apprunner_service.app.arn
  domain_name          = local.hostname
  enable_www_subdomain = false
}

# Points www.<domain> at App Runner
resource "aws_route53_record" "app" {
  count   = local.use_domain ? 1 : 0
  zone_id = data.aws_route53_zone.this[0].zone_id
  name    = local.hostname
  type    = "CNAME"
  ttl     = 300
  records = [aws_apprunner_custom_domain_association.this[0].dns_target]
}

# Lets App Runner issue the free HTTPS certificate.
# These names are only known after the association exists, so first-time setup
# needs two applies (see README).
resource "aws_route53_record" "cert_validation" {
  for_each = local.use_domain ? {
    for r in aws_apprunner_custom_domain_association.this[0].certificate_validation_records : r.name => r
  } : {}
  zone_id = data.aws_route53_zone.this[0].zone_id
  name    = each.value.name
  type    = each.value.type
  ttl     = 300
  records = [each.value.value]
}
