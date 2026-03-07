variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ca-central-1"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "tengri-bot"
}

variable "lightsail_bundle_id" {
  description = "Lightsail bundle ID (small_2_0 = 1GB/$10)"
  type        = string
  default     = "small_2_0"
}

variable "lightsail_blueprint_id" {
  description = "Lightsail blueprint (Ubuntu 22.04)"
  type        = string
  default     = "ubuntu_22_04"
}

variable "github_org" {
  description = "GitHub org or username (for OIDC)"
  type        = string
}

variable "github_repo" {
  description = "GitHub repository name"
  type        = string
  default     = "tengri-bot"
}

