import json  # Add this import at the top

from dotenv import load_dotenv

load_dotenv()

from aws_lambda_powertools.utilities.data_classes.sqs_event import (  # noqa: E402
    SQSRecord,
)
from email_sender.constants.name_change_emails import EmailType  # noqa: E402
from email_sender.usecases.email_usecase import EmailUsecase  # noqa: E402


def create_mock_sqs_record(
    email_template_type: str,
    entity_name: str,
    entity_type: str,
    old_name: str,
    new_name: str,
    to_addresses: list[str],
) -> SQSRecord:
    """Create a mock SQS record for testing."""
    message_body = {
        'email_template_type': email_template_type,
        'entity_name': entity_name,
        'entity_type': entity_type,
        'old_name': old_name,
        'new_name': new_name,
        'to': to_addresses,
    }

    # Create a mock SQS record with properly JSON-encoded body
    return SQSRecord(
        {
            'messageId': 'test_message_id',
            'body': json.dumps(message_body),  # Use json.dumps() instead of str()
            'attributes': {},
            'messageAttributes': {},
            'md5OfBody': '',
            'eventSource': 'aws:sqs',
            'eventSourceARN': 'arn:aws:sqs:region:account:queue',
            'awsRegion': 'ap-southeast-1',
            'receiptHandle': 'test_receipt_handle',
        }
    )


def main():
    # Initialize the email usecase
    email_usecase = EmailUsecase()

    # Test data
    test_record = create_mock_sqs_record(
        email_template_type=EmailType.NAME_CHANGE_REQUEST_RECEIVED.value,
        entity_name='Test Startup Create',
        entity_type='STARTUP',
        old_name='Old Startup Name',
        new_name='New Startup Name',
        to_addresses=['rneljan+2o13kj12b@gmail.com'],
    )

    # Send test email
    print('Sending test email...')
    result = email_usecase.send_email([test_record])
    print(f'Result: {result}')


if __name__ == '__main__':
    main()
