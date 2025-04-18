import { util } from "@aws-appsync/utils";

/**
 * Queries DynamoDB table for entities (startups or enablers)
 * @param {import('@aws-appsync/utils').Context} ctx the context
 * @returns {import('@aws-appsync/utils').DynamoDBQueryRequest} the request
 */
export function request(ctx) {
    const { entityType } = ctx.arguments;

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

    const { items } = ctx.result;
    const entityMap = {};

    // First pass: collect all items for each entity
    items.forEach(item => {
        const [entityType, entityId] = item.hashKey.split('#');

        if (!entityMap[entityId]) {
            entityMap[entityId] = {
                entityType,
                items: []
            };
        }
        entityMap[entityId].items.push(item);
    });

    // Second pass: process each entity's items
    const entities = [];
    Object.entries(entityMap).forEach(([entityId, { entityType, items }]) => {
        const entity = {
            [entityType === 'STARTUP' ? 'startupId' : 'enablerId']: entityId,
            __typename: entityType === 'STARTUP' ? 'Startup' : 'Enabler'
        };

        // Process all items for this entity
        items.forEach(item => {
            if (entityType === 'STARTUP') {
                switch (item.rangeKey) {
                    case 'STARTUP#METADATA':
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
                            industries: item.industries
                        });
                        break;
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
            } else if (entityType === 'ENABLER') {
                switch (item.rangeKey) {
                    case 'ENABLER#METADATA':
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
                            preferredBusinessModels: item.preferredBusinessModels
                        });
                        break;
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

        entities.push(entity);
    });

    return entities;
}
