import { util } from '@aws-appsync/utils';

/**
 * AppSync JS resolver for getMapListAdmin
 * This scans all entities and returns metadata, location, visibility, and request placeholders
 */

/**
 * Queries DynamoDB table for entities (startups or enablers) and name change requests
 * @param {import('@aws-appsync/utils').Context} ctx the context
 * @returns {import('@aws-appsync/utils').DynamoDBQueryRequest} the request
 */
export function request(ctx) {
  return {
    operation: 'Scan',
    index: 'GSI1PK',
  };
}

/**
 * Returns the query items with the specified format
 * @param {import('@aws-appsync/utils').Context} ctx the context
 * @returns {Object} formatted response with entities, counts, and request list
 */
export function response(ctx) {
  if (ctx.error) {
    util.error(ctx.error.message, ctx.error.type);
  }

  const { items } = ctx.result;
  const entityMap = {};
  const requestList = [];
  let startupLength = 0;
  let enablersLength = 0;
  let pendingRequestsLen = 0;

  items.forEach(item => {
    if (item.rangeKey === 'STARTUP#METADATA' || item.rangeKey === 'ENABLER#METADATA') {
      const entityId = item.hashKey.split('#')[1];
      const entityType = item.hashKey.split('#')[0];

    if (!entityMap[entityId]) {
      entityMap[entityId] = {
        id: entityId,
        type: entityType,
      }
    }
  }
  });

  // Process items sequentially
  items.forEach(item => {
    // Handle name change requests
    if (item.rangeKey && item.rangeKey.startsWith('REQUEST#NAME_CHANGE#') && item.isApproved === null) {
      const entityId = item.hashKey.split('#')[1];
      const entityType = item.hashKey.split('#')[0];

      requestList.push({
        requestId: item.requestId,
        requestType: item.requestType,
        entityId: entityId,
        entityType: entityType,
        originalName: item.originalName,
        newName: item.newName,
        isApproved: item.isApproved,
        updatedAt: item.updatedAt
      });

      pendingRequestsLen = pendingRequestsLen + 1;

      const nameChangeRequestStatus = item.isApproved === null ? 'PENDING' : item.isApproved === true ? 'APPROVED' : 'REJECTED';
      if (!entityMap[entityId]) {
        entityMap[entityId] = {
          id: entityId,
          type: entityType,
        };
      }
      entityMap[entityId].nameChangeRequestStatus = nameChangeRequestStatus;
    }

    // Handle entity metadata
    if (item.rangeKey === 'STARTUP#METADATA' || item.rangeKey === 'ENABLER#METADATA') {
      const entityId = item.hashKey.split('#')[1];

      if (item.rangeKey === 'STARTUP#METADATA') {
        entityMap[entityId].name = item.startUpName || '';
      }

      if (item.rangeKey === 'ENABLER#METADATA') {
        entityMap[entityId].name = item.enablerName || '';
      }

      entityMap[entityId].logoObjectKey = item.logoObjectKey || '';
      entityMap[entityId].dateFounded = item.dateFounded || '';
      entityMap[entityId].industries = item.industries || [];
      entityMap[entityId].description = item.description || '';
      entityMap[entityId].location = item.location || {
        address: '',
        latlng: { lat: 0, lng: 0 }
      };
      entityMap[entityId].visibility = item.visibility ?? true;
      startupLength = startupLength + 1;
    }
  });

  // Convert entity map to array
  const mapListArray = Object.values(entityMap);

  return {
    mapList: mapListArray,
    requestList,
    startupLength,
    enablersLength,
    pendingRequestsLen
  };
}
