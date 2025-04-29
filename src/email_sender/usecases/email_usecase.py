import json
from http import HTTPStatus
from typing import Any, Dict, List

import boto3
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.data_classes.sqs_event import SQSRecord
from email_sender.constants.name_change_emails import (
    EmailConstants,
    EmailTemplate,
    EmailType,
)
from shared_modules.models.schema.message import ErrorResponse


class EmailUsecase:
    def __init__(self) -> None:
        self.logger = Logger()
        self.ses_client = boto3.client('ses')

    def send_email(self, records: List[SQSRecord]) -> Dict[str, Any]:
        try:
            for record in records:
                self.logger.info(f'Processing email: {record}')

                message_body = record.json_body
                email_template_type = EmailType(message_body['email_template_type'])
                email_body = EmailTemplate.get_email_template(
                    template_type=email_template_type,
                    entity_name=message_body['entity_name'],
                    entity_type=message_body['entity_type'],
                    old_name=message_body['old_name'],
                    new_name=message_body['new_name'],
                )
                self._send_single_email(
                    from_address=EmailConstants.EMAIL_FROM,
                    to_addresses=message_body['to'],
                    subject=email_body['subject'],
                    body=email_body['body'],
                )

            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'Emails processed successfully'}),
            }

        except Exception as e:
            self.logger.error(f'Error processing email(s): {str(e)}')
            return ErrorResponse(
                response=str(e), status=HTTPStatus.INTERNAL_SERVER_ERROR
            ).model_dump()

    def _send_single_email(
        self, from_address: str, to_addresses: List[str], subject: str, body: str
    ) -> Dict[str, Any]:
        """Send a single email using AWS SES.

        Args:
            from_address: The sender's email address
            to_addresses: List of recipient email addresses
            subject: Email subject line
            body: Email body content

        Returns:
            Dict containing the response from SES
        """
        response = self.ses_client.send_email(
            Source=from_address,
            Destination={'ToAddresses': to_addresses},
            Message={'Subject': {'Data': subject}, 'Body': {'Text': {'Data': body}}},
        )

        self.logger.info(
            'Email sent successfully',
            extra={'messageId': response['MessageId'], 'recipients': to_addresses},
        )

        return response
