import { util } from '@aws-appsync/utils'

export function request(ctx) {
  if (ctx.prev.result.success === false) {
    return {
      success: false,
      message: ctx.prev.result.message
    };
  }

  const { requestId, entityId, entityType, isApproved } = ctx.args.input;
  const { newName } = ctx.prev.result;
  const tableName = ctx.env.TABLE_NAME;
  const updatedAt = util.time.nowISO8601();

  // If not approved, just update the request status
  if (!isApproved) {
    return {
      operation: 'UpdateItem',
      key: util.dynamodb.toMapValues({
        hashKey: `${entityType}#${entityId}`,
        rangeKey: `REQUEST#NAME_CHANGE#${requestId}`
      }),
      update: {
        expression: 'SET #isApproved = :isApproved',
        expressionValues: {
          ':isApproved': util.dynamodb.toDynamoDB(isApproved),
          ':updatedAt': util.dynamodb.toDynamoDB(updatedAt)
        },
        expressionNames: {
          '#isApproved': 'isApproved',
          '#updatedAt': 'updatedAt'
        }
      }
    };
  }

  // If approved, update both the request status and the entity name using a transaction
  const nameField = entityType === 'STARTUP' ? 'startUpName' : 'enablerName';

  return {
    operation: 'TransactWriteItems',
    transactItems: [
      {
        table: tableName,
        operation: 'UpdateItem',
        key: util.dynamodb.toMapValues({
          hashKey: `${entityType}#${entityId}`,
          rangeKey: `REQUEST#NAME_CHANGE#${requestId}`
        }),
        update: {
          expression: 'SET #isApproved = :isApproved',
          expressionValues: {
            ':isApproved': util.dynamodb.toDynamoDB(isApproved),
            ':updatedAt': util.dynamodb.toDynamoDB(updatedAt)
          },
          expressionNames: {
            '#isApproved': 'isApproved',
            '#updatedAt': 'updatedAt'
          }
        }
      },
      {
        table: tableName,
        operation: 'UpdateItem',
        key: util.dynamodb.toMapValues({
          hashKey: `${entityType}#${entityId}`,
          rangeKey: `${entityType}#METADATA`
        }),
        update: {
          expression: `SET #${nameField} = :${nameField}`,
          expressionValues: {
            [`:${nameField}`]: util.dynamodb.toDynamoDB(newName),
            ':updatedAt': util.dynamodb.toDynamoDB(updatedAt)
          },
          expressionNames: {
            [`#${nameField}`]: nameField,
            '#updatedAt': 'updatedAt'
          }
        }
      }
    ]
  };
}

export function response(ctx) {
  if (ctx.error) {
    return {
      success: false,
      message: ctx.error.message
    };
  }

  if (ctx.result.success === false) {
    return {
      success: false,
      message: ctx.result.message
    };
  }

  return {
    success: true,
    message: ctx.args.input.isApproved
      ? 'Name change request approved and entity name updated successfully.'
      : 'Name change request not approved.',
    requestId: ctx.args.input.requestId,
    newName: ctx.prev.result.newName,
    entityType: ctx.args.input.entityType,
    isApproved: ctx.args.input.isApproved,
    originalName: ctx.prev.result.originalName,
    email: ctx.prev.result.email,
  };
}
