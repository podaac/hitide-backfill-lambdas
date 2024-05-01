resource "aws_lambda_function" "backfill_post_step" {
  filename      = "${path.module}/hitide-backfill-post-step-lambda.zip"
  function_name = "${var.prefix}-hitide-backfill-post-step"
  source_code_hash = filebase64sha256("${path.module}/hitide-backfill-lambda.zip")
  handler       = "hitide_backfill_post_step.lambda_handler.lambda_handler"
  role          = var.lambda_role
  runtime       = "python3.9"
  timeout       = var.timeout
  memory_size   = var.memory_size

  architectures = var.architectures

  environment {
    variables = {
      FORGE_STEP_ARN            = var.forge_step_arn
      TIG_STEP_ARN              = var.tig_step_arn
      DMRPP_STEP_ARN            = var.dmrpp_step_arn
      STEP_RETRY                = var.step_retry
      SQS_URL                   = var.sqs_url

      DB_USER_NAME_SSM          = var.user_name
      DB_USER_PASS_SSM          = var.user_pass
      ROOT_USER_SSM             = var.root_user
      ROOT_PASS_SSM             = var.root_pass
      DB_HOST_SSM               = var.db_host
      DB_NAME_SSM               = var.db_name
    }
  }

  vpc_config {
    subnet_ids = var.subnet_ids
    security_group_ids = var.security_group_ids
  }

  tags = local.tags
}

resource "aws_lambda_function" "bootstrap_db" {
  filename      = "${path.module}/hitide-backfill-post-step-lambda.zip"
  function_name = "${var.prefix}-hitide-backfill-bootstrap-db"
  source_code_hash = filebase64sha256("${path.module}/hitide-backfill-lambda.zip")
  handler       = "hitide_backfill_post_step.bootstrap_db.lambda_handler"
  role          = var.lambda_role
  runtime       = "python3.9"
  timeout       = var.timeout
  memory_size   = var.memory_size

  architectures = var.architectures

  environment {
    variables = {
      DB_USER_NAME_SSM = var.user_name
      DB_USER_PASS_SSM = var.user_pass
      ROOT_USER_SSM    = var.root_user
      ROOT_PASS_SSM    = var.root_pass
      DB_HOST_SSM      = var.db_host
      DB_NAME_SSM      = var.db_name
    }
  }

  vpc_config {
    subnet_ids = var.subnet_ids
    security_group_ids = var.security_group_ids
  }

  tags = local.tags
}

resource "aws_lambda_function" "recount-cron" {
  filename      = "${path.module}/hitide-backfill-post-step-lambda.zip"
  function_name = "${var.prefix}-hitide-backfill-recount-cron"
  source_code_hash = filebase64sha256("${path.module}/hitide-backfill-lambda.zip")
  handler       = "hitide_backfill_post_step.recount_cron.lambda_handler"
  role          = var.lambda_role
  runtime       = "python3.9"
  timeout       = 900
  memory_size   = var.memory_size

  architectures = var.architectures

  environment {
    variables = {
      DB_USER_NAME_SSM = var.user_name
      DB_USER_PASS_SSM = var.user_pass
      ROOT_USER_SSM    = var.root_user
      ROOT_PASS_SSM    = var.root_pass
      DB_HOST_SSM      = var.db_host
      DB_NAME_SSM      = var.db_name
    }
  }

  vpc_config {
    subnet_ids = var.subnet_ids
    security_group_ids = var.security_group_ids
  }

  tags = local.tags
}


resource "aws_lambda_function" "backfill_sqs_to_step" {
  filename      = "${path.module}/hitide-backfill-sqs-to-step-lambda.zip"
  function_name = "${var.prefix}-hitide-backfill-sqs-to-step"
  source_code_hash = filebase64sha256("${path.module}/hitide-backfill-lambda.zip")
  handler       = "hitide_backfill_sqs_to_step.lambda_handler.lambda_handler"
  role          = var.lambda_role
  runtime       = "python3.9"
  timeout       = var.timeout
  memory_size   = var.memory_size
  reserved_concurrent_executions = var.reserved_concurrent_executions

  architectures = var.architectures

  environment {
    variables = {
      FORGE_STEP_ARN              = var.forge_step_arn
      TIG_STEP_ARN                = var.tig_step_arn
      DMRPP_STEP_ARN              = var.dmrpp_step_arn
      SQS_URL                     = var.sqs_url
      VISIBILITY_TIMEOUT          = var.message_visibility_timeout
      SSM_THROTTLE_LIMIT          = var.ssm_throttle_limit
    }
  }

  vpc_config {
    subnet_ids = var.subnet_ids
    security_group_ids = var.security_group_ids
  }

  tags = local.tags
}
