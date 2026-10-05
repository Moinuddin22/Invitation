variable "aws_profile" {
  description = "Local AWS CLI profile name"
  type        = string
}

variable "region" {
  type    = string
  default = "ap-south-1"
}

variable "project" {
  type    = string
  default = "haris-mehreen-invite"
}

variable "image_tag" {
  type    = string
  default = "latest"
}

variable "db_instance_class" {
  type    = string
  default = "db.t4g.micro"
}

variable "app_env" {
  description = "Wedding detail overrides passed to the container (WEDDING_DATE_DISPLAY, VENUE_NAME, ...)"
  type        = map(string)
  default     = {}
}
