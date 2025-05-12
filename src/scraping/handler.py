import json
import os
import tempfile

import boto3
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext

from .scraper import WebScraper

logger = Logger()
s3_client = boto3.client('s3')

BUCKET_NAME = 'elevate-rag-documents-06284136e3fa'


@logger.inject_lambda_context
def handler(event: dict, context: LambdaContext) -> dict:
    """
    Lambda handler for web scraping.

    Expected event format:
    {
        "base_url": "https://www.example.com",
        "output_filename": "output.pdf"
    }
    """
    try:
        # Extract parameters from event
        output_filename = event.get('output_filename', 'output.pdf')

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_pdf_path = os.path.join(temp_dir, output_filename)

            # Initialize and run scraper
            scraper = WebScraper()
            scraper.crawl()  # Using the new crawl method
            scraper.save_pdf(temp_pdf_path)

            # Upload to S3
            try:
                logger.info(f'Uploading PDF to S3 bucket: {BUCKET_NAME}')
                s3_key = f'scraped_documents/{output_filename}'
                s3_client.upload_file(
                    temp_pdf_path, BUCKET_NAME, s3_key, ExtraArgs={'ContentType': 'application/pdf'}
                )
                s3_url = f's3://{BUCKET_NAME}/{s3_key}'
                logger.info(f'Successfully uploaded PDF to {s3_url}')

                return {
                    'statusCode': 200,
                    'body': json.dumps(
                        {
                            'message': 'Scraping and upload completed successfully',
                            'pages_scraped': len(scraper.visited),
                            'priority_pages_scraped': sum(
                                1 for url in scraper.visited if url in scraper.PRIORITY_URLS
                            ),
                            'output_file': output_filename,
                            's3_url': s3_url,
                        }
                    ),
                }

            except Exception as s3_error:
                logger.error(f'Failed to upload PDF to S3: {str(s3_error)}')
                raise s3_error

    except Exception as e:
        logger.exception('Error during scraping or upload')
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}
