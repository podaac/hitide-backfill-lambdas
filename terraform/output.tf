output "backfill_post_step_task_arn" {
  value = aws_lambda_function.backfill_post_step.arn
}

output "backfill_post_step_function_name" {
  value = aws_lambda_function.backfill_post_step.function_name
}

output "backfill_sqs_to_step_task_arn" {
  value = aws_lambda_function.backfill_sqs_to_step.arn
}

output "backfill_sqs_to_step_function_name" {
  value = aws_lambda_function.backfill_sqs_to_step.function_name
}