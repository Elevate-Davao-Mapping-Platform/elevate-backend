import { util } from '@aws-appsync/utils'

export function request(ctx) {
  const { entityId, entityType, newName, originalName } = ctx.args.input

  const requestId = util.autoKsuid()
  const timestamp = util.time.nowISO8601()
  const ksuid = util.autoKsuid()

  return {
    operation: 'PutItem',
    key: {
      hashKey: util.dynamodb.toDynamoDB(`${entityType}#${entityId}`),
      rangeKey: util.dynamodb.toDynamoDB(`REQUEST#NAME_CHANGE#${requestId}`)
    },
    attributeValues: {
      requestId: util.dynamodb.toDynamoDB(requestId),
      entityId: util.dynamodb.toDynamoDB(entityId),
      entityType: util.dynamodb.toDynamoDB(entityType),
      originalName: util.dynamodb.toDynamoDB(originalName),
      newName: util.dynamodb.toDynamoDB(newName),
      isApproved: util.dynamodb.toDynamoDB(null),
      requestType: util.dynamodb.toDynamoDB('NAME_CHANGE'),
      createdAt: util.dynamodb.toDynamoDB(timestamp),
      updatedAt: util.dynamodb.toDynamoDB(timestamp),
      GSI1PK: util.dynamodb.toDynamoDB(ksuid),
      GSI2PK: util.dynamodb.toDynamoDB(requestId),
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

  const { requestId } = ctx.result

  return {
    id: requestId,
    success: true,
    message: 'Name change request submitted successfully.'
  }
}
