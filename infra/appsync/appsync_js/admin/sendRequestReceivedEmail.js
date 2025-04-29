import { util } from '@aws-appsync/utils'

export function request(ctx) {
	const { originalName, newName, entityType, email } = ctx.prev.result

	const accountId = ctx.env.ACCOUNT_ID
	const queueName = ctx.env.EMAIL_QUEUE_NAME
	const queueUrl = ctx.env.EMAIL_QUEUE_URL

	const emailTemplateType = 'name_change_request_received'

	const requestBody = {
		'email_template_type': emailTemplateType,
		'entity_name': originalName,
		'entity_type': entityType,
		'old_name': originalName,
		'new_name': newName,
		'to': [email],
	}

	let body = 'Action=SendMessage&Version=2012-11-05'
	const messageBody = util.urlEncode(JSON.stringify(requestBody))
	const queueUrlEncoded = util.urlEncode(queueUrl)
	body = `${body}&MessageBody=${messageBody}&QueueUrl=${queueUrlEncoded}`

	return {
		version: '2018-05-29',
		method: 'POST',
		resourcePath: `/${accountId}/${queueName}`,
		params: {
			body,
			headers: {
				'content-type': 'application/x-www-form-urlencoded',
			},
		},
	}
}

export function response(ctx) {
    if (ctx.error) {
        return {
            id: null,
            message: ctx.error.message,
            success: false
        };
    }

    const { id, message, success } = ctx.prev.result
    return {
        id,
        message,
        success
    };
}
