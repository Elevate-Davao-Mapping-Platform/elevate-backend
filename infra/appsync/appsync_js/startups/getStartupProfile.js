import { util } from "@aws-appsync/utils";

/**
 * Queries DynamoDB table for startup
 * @param {import('@aws-appsync/utils').Context} ctx the context
 * @returns {import('@aws-appsync/utils').DynamoDBQueryRequest} the request
 */
export function request(ctx) {
    return {
        operation: "Query",
        query: {
            expression:
                "hashKey = :hashKey",
            expressionValues: util.dynamodb.toMapValues({
                ":hashKey": `STARTUP#${ctx.args.startupId}`,
            }),
        },
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
    if (items.length === 0) {
        util.error("Startup not found", "NotFound");
    }

    const startupId = ctx.arguments.startupId;

    // Initialize the startup object
    const startup = {
        startupId: startupId,
    };

    const suggestions = [];

    // Process each item based on its rangeKey
    items.forEach(item => {
        switch (item.rangeKey) {
            case 'STARTUP#METADATA':
                Object.assign(startup, {
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
                startup.contacts = item.contacts;
                break;
            case 'STARTUP#MILESTONES':
                startup.milestones = item.milestones;
                break;
            case 'STARTUP#FOUNDERS':
                startup.founders = item.founders;
                break;
        }

    });

    startup.suggestions = suggestions;

    return startup;
}
