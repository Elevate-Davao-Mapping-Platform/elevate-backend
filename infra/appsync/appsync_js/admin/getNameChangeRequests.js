import { util } from '@aws-appsync/utils'

export function request(ctx) {
  const { isApproved } = ctx.arguments;
  const baseRequest = {
    operation: 'Scan',
    index: 'GSI2PK'
  };

  if (isApproved === undefined) {
    return baseRequest;
  }

  return {
    ...baseRequest,
    filter: {
      expression: 'isApproved = :isApproved',
      expressionValues: { ':isApproved': util.dynamodb.toDynamoDB(isApproved) }
    }
  };
}

export function response(ctx) {
  if (ctx.error) {
    util.error(ctx.error.message, ctx.error.type);
  }

  const { items } = ctx.result;

  return items.map(item => {
    const [itemEntityType, itemEntityId] = item.hashKey.split('#');

    return {
      entityId: itemEntityId,
      entityType: itemEntityType === 'STARTUP' ? 'STARTUP' : 'ENABLER',
      requestId: item.requestId,
      originalName: item.originalName,
      newName: item.newName,
      isApproved: item.isApproved,
      createdAt: item.createdAt,
      updatedAt: item.updatedAt,
      requestType: item.requestType
    };
  });
}
