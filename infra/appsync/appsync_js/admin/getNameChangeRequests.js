import { util } from '@aws-appsync/utils'

export function request(ctx) {
  const { isApproved } = ctx.arguments;

  return {
    operation: 'Scan',
    index: 'GSI2PK',
    ...(isApproved && {
      filter: {
        expression: 'isApproved = :isApproved',
        expressionValues: { ':isApproved': util.dynamodb.toDynamoDB(isApproved) }
      }
    })
  }
}

export function response(ctx) {
  if (ctx.error) {
    util.error(ctx.error.message, ctx.error.type);
  }

  const { items } = ctx.result;
  const entityMap = {};

  items.forEach(item => {
    const [itemEntityType, itemEntityId] = item.hashKey.split('#');

    if (itemEntityType === 'STARTUP') {
      item.entityType = 'STARTUP';
    } else if (itemEntityType === 'ENABLER') {
      item.entityType = 'ENABLER';
    }

    if (!entityMap[itemEntityId]) {
      entityMap[itemEntityId] = {
        entityType: itemEntityType,
        items: []
      };
    }

    entityMap[itemEntityId].items.push(item);
  })

  const entities = [];

  Object.entries(entityMap).forEach(([itemEntityId, { entityType: itemEntityType, items }]) => {
    const entity = {
      entityId: itemEntityId,
      entityType: itemEntityType,
    };

    items.forEach(item => {
      entity.requestId = item.requestId;
      entity.originalName = item.originalName;
      entity.newName = item.newName;
      entity.isApproved = item.isApproved;
      entity.createdAt = item.createdAt;
    })

    entities.push(entity);
  })

  return entities;
}
