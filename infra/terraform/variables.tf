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

variable "domain_name" {
  description = "Domain bought in Route 53, e.g. harisweds.com. Leave empty to use the default App Runner URL."
  type        = string
  default     = ""
}

variable "subdomain" {
  description = "Host the app is served on, e.g. www -> www.harisweds.com"
  type        = string
  default     = "www"
}
