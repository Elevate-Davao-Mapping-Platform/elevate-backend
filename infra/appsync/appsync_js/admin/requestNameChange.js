import { util } from '@aws-appsync/utils'

export function request(ctx) {
  const { entityId, entityType, newName } = ctx.args.input

  const requestId = util.autoKsuid() 
  const timestamp = util.time.nowISO8601()

  return {
    operation: 'PutItem',
    key: {
      PK: util.dynamodb.toDynamoDB(`${entityType}#${entityId}`),
      SK: util.dynamodb.toDynamoDB(`REQUEST#NAME_CHANGE#${requestId}`)
    },
    attributeValues: {
      requestId: util.dynamodb.toDynamoDB(requestId),
      entityId: util.dynamodb.toDynamoDB(entityId),
      entityType: util.dynamodb.toDynamoDB(entityType),
      newName: util.dynamodb.toDynamoDB(newName),
      isApproved: util.dynamodb.toDynamoDB(false),
      requestType: util.dynamodb.toDynamoDB('NAME_CHANGE'),
      createdAt: util.dynamodb.toDynamoDB(timestamp),
      updatedAt: util.dynamodb.toDynamoDB(timestamp)
    }
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
  return {
    success: true,
    message: 'Name change request submitted successfully.'
  }
}
