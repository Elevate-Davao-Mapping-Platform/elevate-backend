import { util } from "@aws-appsync/utils";

/**
 * Queries DynamoDB table for entities (startups or enablers)
 * @param {import('@aws-appsync/utils').Context} ctx the context
 * @returns {import('@aws-appsync/utils').DynamoDBQueryRequest} the request
 */
export function request(ctx) {
    const { filterEntityType } = ctx.arguments;

    return {
        operation: "Scan",
        index: "GSI1PK",
        ...(filterEntityType && {
            filter: {
                expression: "begins_with(rangeKey, :filterEntityType)",
                expressionValues: {
                    ":filterEntityType": util.dynamodb.toDynamoDB(`${filterEntityType}#`)
                }
            }
        })
    };
}

/**
 * Returns the query items
 * @param {import('@aws-appsync/utils').Context} ctx the context
 * @returns {[*]} a flat list of result items
 */
export function response(ctx) {
    if (ctx.error) {
        util.error(ctx.error.message, ctx.error.type);
    }

    const { entityId, entityType } = ctx.arguments;

    const { items } = ctx.result;
    const entityMap = {};
    const savedProfiles = {}; // Track saved profiles using an object instead of Set

    // First pass: collect all items for each entity
    items.forEach(item => {
        const [itemEntityType, itemEntityId] = item.hashKey.split('#');

        // Check if this is a saved profile entry for the current user
        if (entityId && entityType &&
            item.hashKey === `${entityType}#${entityId}` &&
            item.rangeKey.includes('SAVED_PROFILE')) {
            // Extract the saved profile ID from rangeKey (format: ENTITY_TYPE#SAVED_PROFILE#PROFILE_TYPE#PROFILE_ID)
            const savedProfileId = item.rangeKey.split('#')[3];
            savedProfiles[savedProfileId] = true; // Use object property instead of Set.add()
        }

        if (!entityMap[itemEntityId]) {
            entityMap[itemEntityId] = {
                entityType: itemEntityType,
                items: []
            };
        }
        entityMap[itemEntityId].items.push(item);
    });

    // Second pass: process each entity's items
    const entities = [];
    Object.entries(entityMap).forEach(([itemEntityId, { entityType: itemEntityType, items }]) => {
        const entity = {
            [itemEntityType === 'STARTUP' ? 'startupId' : 'enablerId']: itemEntityId,
            __typename: itemEntityType === 'STARTUP' ? 'Startup' : 'Enabler',
            isSaved: savedProfiles[itemEntityId] === true // Check if profile exists in object
        };

        // Process all items for this entity
        items.forEach(item => {
            if (itemEntityType === 'STARTUP') {
                switch (item.rangeKey) {
                    case 'STARTUP#METADATA': {
                        Object.assign(entity, {
                            startUpName: item.startUpName,
                            email: item.email,
                            logoObjectKey: item.logoObjectKey,
                            dateFounded: item.dateFounded,
                            startupStage: item.startupStage,
                            description: item.description,
                            location: item.location,
                            revenueModel: item.revenueModel,
                            createdAt: item.createdAt,
                            industries: item.industries,
                            visibility: item.visibility === null ? true : item.visibility,
                            updatedAt: item.updatedAt ?? item.createdAt
                        });
                        break;
                    }
                    case 'STARTUP#CONTACTS':
                        entity.contacts = item.contacts || [];
                        break;
                    case 'STARTUP#MILESTONES':
                        entity.milestones = item.milestones;
                        break;
                    case 'STARTUP#FOUNDERS':
                        entity.founders = item.founders;
                        break;
                }
            } else if (itemEntityType === 'ENABLER') {
                switch (item.rangeKey) {
                    case 'ENABLER#METADATA': {
                        Object.assign(entity, {
                            enablerName: item.enablerName,
                            email: item.email,
                            logoObjectKey: item.logoObjectKey,
                            dateFounded: item.dateFounded,
                            organizationType: item.organizationType,
                            description: item.description,
                            location: item.location,
                            industryFocus: item.industryFocus,
                            supportType: item.supportType,
                            fundingStageFocus: item.fundingStageFocus,
                            investmentAmount: item.investmentAmount,
                            startupStagePreference: item.startupStagePreference,
                            preferredBusinessModels: item.preferredBusinessModels,
                            visibility: item.visibility === null ? true : item.visibility,
                            updatedAt: item.updatedAt ?? item.createdAt
                        });
                        break;
                    }
                    case 'ENABLER#CONTACTS':
                        entity.contacts = item.contacts || [];
                        break;
                    case 'ENABLER#INVESTMENT_CRITERIA':
                        entity.investmentCriteria = item.investmentCriteria;
                        break;
                    case 'ENABLER#PORTFOLIO':
                        entity.portfolio = item.portfolio;
                        break;
                }
            }
        });

        if (entity.visibility !== false) {
            entities.push(entity);
        }
    });

    return entities;
}
