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
  let pendingRequestsLength = 0;

  // Process items sequentially
  items.forEach(item => {
    const entityId = item.hashKey.split('#')[1];
    const entityType = item.hashKey.split('#')[0];

    // First pass: create entity map
    if (!entityMap[entityId]) {
      entityMap[entityId] = {
        entityType: entityType,
        [entityType === 'STARTUP' ? 'startupId' : 'enablerId']: entityId,
        __typename: entityType === 'STARTUP' ? 'Startup' : 'Enabler',
      }
    }

    // Second pass: handle name change requests
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

      pendingRequestsLength = pendingRequestsLength + 1;

      entityMap[entityId].nameChangeRequestStatus = {
        requestId: item.requestId,
        requestType: item.requestType,
        entityId: entityId,
        entityType: entityType,
        originalName: item.originalName,
        newName: item.newName,
        isApproved: item.isApproved,
        updatedAt: item.updatedAt
      };
    }

    // Third pass: handle entity metadata
    if (entityType === 'STARTUP') {
      switch (item.rangeKey) {
        case 'STARTUP#METADATA':
          entityMap[entityId].startUpName = item.startUpName;
          entityMap[entityId].email = item.email;
          entityMap[entityId].logoObjectKey = item.logoObjectKey;
          entityMap[entityId].dateFounded = item.dateFounded;
          entityMap[entityId].startupStage = item.startupStage;
          entityMap[entityId].description = item.description;
          entityMap[entityId].location = item.location;
          entityMap[entityId].revenueModel = item.revenueModel;
          entityMap[entityId].createdAt = item.createdAt;
          entityMap[entityId].industries = item.industries;
          entityMap[entityId].visibility = item.visibility === null ? true : item.visibility;
          entityMap[entityId].updatedAt = item.updatedAt ?? item.createdAt;
          startupLength = startupLength + 1;
          break;
        case 'STARTUP#CONTACTS':
          entityMap[entityId].contacts = item.contacts;
          break;
        case 'STARTUP#MILESTONES':
          entityMap[entityId].milestones = item.milestones;
          break;
        case 'STARTUP#FOUNDERS':
          entityMap[entityId].founders = item.founders;
          break;
      }
    } else if (entityType === 'ENABLER') {
      switch (item.rangeKey) {
        case 'ENABLER#METADATA':
          entityMap[entityId].enablerName = item.enablerName;
          entityMap[entityId].email = item.email;
          entityMap[entityId].logoObjectKey = item.logoObjectKey;
          entityMap[entityId].dateFounded = item.dateFounded;
          entityMap[entityId].organizationType = item.organizationType;
          entityMap[entityId].description = item.description;
          entityMap[entityId].location = item.location;
          entityMap[entityId].industryFocus = item.industryFocus;
          entityMap[entityId].supportType = item.supportType;
          entityMap[entityId].fundingStageFocus = item.fundingStageFocus;
          entityMap[entityId].investmentAmount = item.investmentAmount;
          entityMap[entityId].startupStagePreference = item.startupStagePreference;
          entityMap[entityId].preferredBusinessModels = item.preferredBusinessModels;
          entityMap[entityId].visibility = item.visibility === null ? true : item.visibility;
          entityMap[entityId].updatedAt = item.updatedAt ?? item.createdAt;
          enablersLength = enablersLength + 1;
          break;
        case 'ENABLER#CONTACTS':
          entityMap[entityId].contacts = item.contacts;
          break;
        case 'ENABLER#INVESTMENT_CRITERIA':
          entityMap[entityId].investmentCriteria = item.investmentCriteria;
          break;
        case 'ENABLER#PORTFOLIO':
          entityMap[entityId].portfolio = item.portfolio;
          break;
      }
    }
  });

  // Convert entity map to array
  const mapListArray = Object.values(entityMap);

  return {
    mapList: mapListArray,
    requestList,
    startupLength,
    enablersLength,
    pendingRequestsLength
  };
}
