import { util } from "@aws-appsync/utils";

/**
 * Queries DynamoDB table for startup
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
 * Returns the query items
 * @param {import('@aws-appsync/utils').Context} ctx the context
 * @returns {[*]} a flat list of result items
 */
export function response(ctx) {
    if (ctx.error) {
        util.error(ctx.error.message, ctx.error.type);
    }

    const items = ctx.result.items;
    const startups = [];
    let currentStartup = null;
    let currentStartupId = null;

    // Process items sequentially, assuming related items are adjacent
    items.forEach(item => {
        const startupId = item.hashKey.split('#')[1];

        // If this is a new startup, create a new startup object
        if (startupId !== currentStartupId) {
            if (currentStartup) {
                startups.push(currentStartup);
            }
            currentStartup = { startupId };
            currentStartupId = startupId;
        }

        // Add item data to current startup based on rangeKey
        switch (item.rangeKey) {
            case 'STARTUP#METADATA':
                Object.assign(currentStartup, {
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
                currentStartup.contacts = item.contacts;
                break;
            case 'STARTUP#INDUSTRIES':
                currentStartup.industry = item.industries;
                break;
            case 'MILESTONES':
                currentStartup.milestones = item.milestones;
                break;
            case 'STARTUP#FOUNDERS':
                currentStartup.founders = item.founders;
                break;
        }
    });

    // Add the last startup if exists
    if (currentStartup) {
        startups.push(currentStartup);
    }

    return startups;
}
