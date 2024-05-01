resource "aws_cloudwatch_event_rule" "recount_cron_every_hour" {
    name = "${var.prefix}-recount-cron"
    description = "Fires every 60 minutes"
    schedule_expression = "rate(60 minutes)"
}

resource "aws_cloudwatch_event_target" "recount_cron_every_hour" {
    rule = aws_cloudwatch_event_rule.recount_cron_every_hour.name
    target_id = "${var.prefix}-recount_cron"
    arn = aws_lambda_function.recount-cron.arn
}

resource "aws_lambda_permission" "allow_recount_cron_every_hour" {
    statement_id = "AllowExecutionFromCloudWatch"
    action = "lambda:InvokeFunction"
    function_name = aws_lambda_function.recount-cron.function_name
    principal = "events.amazonaws.com"
    source_arn = aws_cloudwatch_event_rule.recount_cron_every_hour.arn
}