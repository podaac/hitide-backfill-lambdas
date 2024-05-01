variable "aws_profile" {
  type    = string
  default = null
}

variable "prefix" {
  type = string
}

variable "lambda_role" {
  type = string
}

variable "layers" {
  default = []
  type = list(string)
}

variable "app_name" {
  default = "backfill_sqs_to_step"
}

variable "default_tags" {
  type = map(string)
  default = {}
}

variable "memory_size" {
  type = number
  default = 256
}

variable "timeout" {
  type = number
  default = 120
}

variable "forge_step_arn" { 
  type = string
}

variable "tig_step_arn" {
  type = string
}

variable "dmrpp_step_arn" {
  type = string
}

variable "sqs_url" {
  type = string
}

variable "region" {
  type = string
}

variable "step_retry"{
  type = number
  default = 3
}

variable "subnet_ids" {}
variable "security_group_ids" {}

variable "user_name" {}
variable "user_pass" {}
variable "root_user" {}
variable "root_pass" {}
variable "db_host" {}
variable "db_name" {}

variable "reserved_concurrent_executions"{
  type = number
  default = -1
}

variable "message_visibility_timeout" {
  type = number
  default = 1200
}

variable "ssm_throttle_limit" {}

variable architectures {
  default = ["arm64"]
  type = list
}
