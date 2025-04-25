import { util } from "@aws-appsync/utils";

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
        operation: "Scan",
        index: "GSI1PK"
    };
}

/**
 * Returns the query items with the specified format
 * @param {import('@aws-appsync/utils').Context} ctx the context
 * @returns {Object} formatted response with mapList, requestList, and counts
 */
export function response(ctx) {
    if (ctx.error) {
        util.error(ctx.error.message, ctx.error.type);
    }

    const { items } = ctx.result;
    const mapList = [];
    const requestList = [];
    let currentEntity = null;
    let currentEntityId = null;
    let startupLength = 0;
    let enablersLength = 0;
    let pendingRequestsLen = 0;

    // Process items sequentially, assuming related items are adjacent
    items.forEach(item => {
        const currentEntityType = item.hashKey.split('#')[0];
        const entityId = item.hashKey.split('#')[1];

        // Handle name change requests
        if (item.rangeKey === 'NAME_CHANGE_REQUEST') {
            requestList.push({
                requestId: item.requestId,
                requestType: item.requestType,
                entityId: item.entityId,
                entityType: item.entityType,
                originalName: item.originalName,
                newName: item.newName,
                isApproved: item.isApproved,
                updatedAt: item.updatedAt
            });
            
            if (!item.isApproved) {
                pendingRequestsLen++;
            }
            return;
        }

        // If this is a new entity, create a new entity object
        if (entityId !== currentEntityId) {
            if (currentEntity) {
                mapList.push(currentEntity);
            }
            
            currentEntity = {
                id: entityId,
                role: currentEntityType,
                name: '',
                logoObjectKey: '',
                dateFounded: '',
                industries: [],
                description: '',
                location: {
                    address: '',
                    latlng: {
                        lat: 0,
                        lng: 0
                    }
                },
                nameChangeRequestStatus: {
                    isApproved: true
                },
                visibility: true
            };
            
            currentEntityId = entityId;
            
            // Count entities by type
            if (currentEntityType === 'STARTUP') {
                startupLength++;
            } else if (currentEntityType === 'ENABLER') {
                enablersLength++;
            }
        }

        // Add item data based on rangeKey and entity type
        if (currentEntityType === 'STARTUP') {
            switch (item.rangeKey) {
                case 'STARTUP#METADATA':
                    Object.assign(currentEntity, {
                        name: item.startUpName,
                        logoObjectKey: item.logoObjectKey,
                        dateFounded: item.dateFounded,
                        industries: item.industries || [],
                        description: item.description,
                        location: item.location || {
                            address: '',
                            latlng: { lat: 0, lng: 0 }
                        },
                        visibility: item.visibility !== false
                    });
                    break;
            }
        } else if (currentEntityType === 'ENABLER') {
            switch (item.rangeKey) {
                case 'ENABLER#METADATA':
                    Object.assign(currentEntity, {
                        name: item.enablerName,
                        logoObjectKey: item.logoObjectKey,
                        dateFounded: item.dateFounded,
                        industries: item.industryFocus || [],
                        description: item.description,
                        location: item.location || {
                            address: '',
                            latlng: { lat: 0, lng: 0 }
                        },
                        visibility: item.visibility !== false
                    });
                    break;
            }
        }
    });

    // Add the last entity if exists
    if (currentEntity) {
        mapList.push(currentEntity);
    }

    return {
        mapList,
        requestList,
        startupLength,
        enablersLength,
        pendingRequestsLen
    };
}
  