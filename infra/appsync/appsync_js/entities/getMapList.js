import { util } from "@aws-appsync/utils";

/**
 * Queries DynamoDB table for entities (startups or enablers)
 * @param {import('@aws-appsync/utils').Context} ctx the context
 * @returns {import('@aws-appsync/utils').DynamoDBQueryRequest} the request
 */
export function request(ctx) {
    const entityType = ctx.arguments.entityType;

    return {
        operation: "Scan",
        index: "GSI1PK",
        ...(entityType && {
            filter: {
                expression: "begins_with(rangeKey, :entityType)",
                expressionValues: {
                    ":entityType": util.dynamodb.toDynamoDB(`${entityType}#`)
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

    const items = ctx.result.items;
    const entities = [];
    let currentEntity = null;
    let currentEntityId = null;

    // Process items sequentially, assuming related items are adjacent
    items.forEach(item => {
        const currentEntityType = item.hashKey.split('#')[0];
        const entityId = item.hashKey.split('#')[1];

        // If this is a new entity, create a new entity object
        if (entityId !== currentEntityId) {
            if (currentEntity) {
                entities.push(currentEntity);
            }
            currentEntity = currentEntityType === 'STARTUP'
                ? { startupId: entityId, __typename: 'Startup' }
                : { enablerId: entityId, __typename: 'Enabler' };
            currentEntityId = entityId;
        }

        // Add item data based on rangeKey and entity type
        if (currentEntityType === 'STARTUP') {
            switch (item.rangeKey) {
                case 'STARTUP#METADATA':
                    Object.assign(currentEntity, {
                        startUpName: item.startUpName,
                        email: item.email,
                        logoObjectKey: item.logoObjectKey,
                        dateFounded: item.dateFounded,
                        startupStage: item.startupStage,
                        description: item.description,
                        location: item.location,
                        revenueModel: item.revenueModel,
                        createdAt: item.createdAt
                    });
                    break;
                case 'STARTUP#CONTACTS':
                    currentEntity.contacts = item.contacts;
                    break;
                case 'STARTUP#INDUSTRIES':
                    currentEntity.industry = item.industries;
                    break;
                case 'STARTUP#MILESTONES':
                    currentEntity.milestones = item.milestones;
                    break;
                case 'STARTUP#FOUNDERS':
                    currentEntity.founders = item.founders;
                    break;
            }
        } else if (currentEntityType === 'ENABLER') {
            switch (item.rangeKey) {
                case 'ENABLER#METADATA':
                    Object.assign(currentEntity, {
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
                        preferredBusinessModels: item.preferredBusinessModels
                    });
                    break;
                case 'ENABLER#CONTACTS':
                    currentEntity.contacts = item.contacts;
                    break;
                case 'ENABLER#INVESTMENT_CRITERIA':
                    currentEntity.investmentCriteria = item.investmentCriteria;
                    break;
                case 'ENABLER#PORTFOLIO':
                    currentEntity.portfolio = item.portfolio;
                    break;
                }
            }
    });

    // Add the last entity if exists
    if (currentEntity) {
        entities.push(currentEntity);
    }

    return entities;
}
