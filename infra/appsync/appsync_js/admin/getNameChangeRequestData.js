import { util } from '@aws-appsync/utils'

export function request(ctx) {
  let { requestId, entityId, entityType } = ctx.args.input;
  const tableName = ctx.env.TABLE_NAME;

  // If requestId not provided in input, get it from previous pipeline result
  if (!requestId && ctx.prev.result) {
    requestId = ctx.prev.result.id;
  }

  return {
    operation: 'BatchGetItem',
    tables: {
      [tableName]: {
        keys: [
          util.dynamodb.toMapValues({
            hashKey: `${entityType}#${entityId}`,
            rangeKey: `REQUEST#NAME_CHANGE#${requestId}`
          }),
          util.dynamodb.toMapValues({
            hashKey: `${entityType}#${entityId}`,
            rangeKey: `${entityType}#METADATA`
          }),
        ]
      }
    }
  };
}

export function response(ctx) {
  if (ctx.error) {
    return {
      success: false,
      message: ctx.error.message
    };
  }

  // Get the results from the table
  const tableName = ctx.env.TABLE_NAME;
  const results = ctx.result.data[tableName];

  // return error if no items are found
  if (!results || results.length === 0) {
    return {
      success: false,
      message: 'No item found'
    };
  }

  const requestResult = results[0];
  const metadataResult = results[1];

  return {
    success: true,
    requestId: requestResult?.requestId,
    entityId: requestResult?.entityId,
    entityType: requestResult?.entityType,
    isApproved: requestResult?.isApproved,
    newName: requestResult?.newName,
    originalName: requestResult?.originalName,
    email: metadataResult?.email
  };
}
