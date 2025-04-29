from email.header import Header
from email.utils import formataddr
from enum import Enum
from typing import Dict


class EmailType(Enum):
    NAME_CHANGE_REQUEST_RECEIVED = 'name_change_request_received'
    NAME_CHANGE_REQUEST_APPROVED = 'name_change_request_approved'
    NAME_CHANGE_REQUEST_REJECTED = 'name_change_request_rejected'


class EmailConstants:
    name = 'Elevate Davao'
    email_address = 'elevate.davao.map@gmail.com'
    EMAIL_FROM = formataddr((str(Header(name, 'utf-8')), email_address))


class EmailTemplate:
    # Common elements
    ELEVATE_SIGNATURE = """

Warm regards,
The Elevate Team
elevate.davao.map@gmail.com
Confidentiality Notice: This email and any information contained within it are confidential and intended solely for the recipient. Please do not share or forward its contents without prior consent from Elevate."""

    # Name Change Request Templates
    NAME_CHANGE_REQUEST_RECEIVED = {
        'subject': 'Your Name Change Request Is Being Reviewed',
        'body': """Hi {entity_name},

Thanks for submitting a request to update your {entity_type} name from {old_name} to {new_name}.

Our team is currently reviewing your request to ensure accuracy and legitimacy. You'll receive an update once a decision has been made, typically within a few business days.

In the meantime, your current profile remains active and visible to others in the Elevate ecosystem.

Thanks for helping us keep the ecosystem up to date and trustworthy."""
        + ELEVATE_SIGNATURE,
    }

    NAME_CHANGE_REQUEST_APPROVED = {
        'subject': 'Your Name Change Request Has Been Approved',
        'body': """Hi {entity_name},

Great news! Your request to change your {entity_type} name from {old_name} to {new_name} has been successfully reviewed and approved by our team.

Your profile has now been updated across the Elevate ecosystem, so partners, enablers, and investors will see your new name moving forward.

Thank you for keeping your profile accurate and up to date. If you need to make further edits or have any questions, feel free to reach out."""
        + ELEVATE_SIGNATURE,
    }

    NAME_CHANGE_REQUEST_REJECTED = {
        'subject': "Your Name Change Request Couldn't Be Approved",
        'body': """Hi {entity_name},

We've reviewed your request to update your {entity_type} name from {old_name} to {new_name}. Unfortunately, we weren't able to approve this request at this time.

This could be due to incomplete or unverifiable information submitted. If you believe this was an error or would like to re-submit with additional context or documents, feel free to do so.

We're here to help maintain accuracy and transparency within the Elevate platform. Thanks for your understanding!"""
        + ELEVATE_SIGNATURE,
    }

    TEMPLATE_MAPPING = {
        EmailType.NAME_CHANGE_REQUEST_RECEIVED: NAME_CHANGE_REQUEST_RECEIVED,
        EmailType.NAME_CHANGE_REQUEST_APPROVED: NAME_CHANGE_REQUEST_APPROVED,
        EmailType.NAME_CHANGE_REQUEST_REJECTED: NAME_CHANGE_REQUEST_REJECTED,
    }

    @classmethod
    def get_email_template(
        cls,
        template_type: EmailType,
        entity_name: str,
        entity_type: str,
        old_name: str,
        new_name: str,
    ) -> Dict[str, str]:
        """
        Get a formatted name change email template with the provided parameters.

        Args:
            template_type: Type of template (EmailType enum)
            entity_name: Name of the entity requesting the change
            entity_type: Type of entity (Startup/Organization)
            old_name: Current name of the entity
            new_name: Requested new name

        Returns:
            Dict containing formatted subject and body

        Raises:
            ValueError: If template_type is not a valid EmailType
        """
        template = EmailTemplate.TEMPLATE_MAPPING[template_type]

        return {
            'subject': template['subject'],
            'body': template['body'].format(
                entity_name=entity_name,
                entity_type=entity_type,
                old_name=old_name,
                new_name=new_name,
            ),
        }
