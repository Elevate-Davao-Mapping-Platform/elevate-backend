from typing import Any, Dict

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.data_classes import SQSEvent, event_source
from aws_lambda_powertools.utilities.typing import LambdaContext
from email_sender.usecases.email_usecase import EmailUsecase

logger = Logger()


@logger.inject_lambda_context
@event_source(data_class=SQSEvent)
def handler(event: SQSEvent, context: LambdaContext) -> Dict[str, Any]:
    """
    Lambda handler to process SQS messages and send emails via SES.
    Expected SQS message format:
    {
        "to": ["email@example.com"],
        "subject": "Email Subject",
        "body": "Email body content",
        "from": "sender@yourdomain.com"  # Must be verified in SES
    }
    """
    _ = context
    email_usecase = EmailUsecase()
    return email_usecase.send_email(event.records)
