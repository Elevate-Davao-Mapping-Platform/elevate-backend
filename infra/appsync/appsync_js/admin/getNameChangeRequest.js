import { util } from '@aws-appsync/utils'

export function request(ctx) {
  const { requestId, entityId, entityType } = ctx.args.input;

  return {
    operation: 'GetItem',
    key: util.dynamodb.toMapValues({
      hashKey: `${entityType}#${entityId}`,
      rangeKey: `REQUEST#NAME_CHANGE#${requestId}`
    }),
  };
}

export function response(ctx) {
  if (ctx.error) {
    return {
      success: false,
      message: ctx.error.message
    };
  }

  // return error if no item is found
  if (!ctx.result) {
    return {
      success: false,
      message: 'No item found'
    };
  }

  return {
    success: true,
    requestId: ctx.result.requestId,
    entityId: ctx.result.entityId,
    entityType: ctx.result.entityType,
    isApproved: ctx.args.input.isApproved,
    newName: ctx.result.newName
  };
} 