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
    const startupId = ctx.arguments.startupId;

    // Initialize the startup object
    const startup = {
        startupId: startupId,
    };

    // Process each item based on its rangeKey
    items.forEach(item => {
        switch (item.rangeKey) {
            case 'METADATA':
                Object.assign(startup, {
                    startUpName: item.startUpName,
                    email: item.email,
                    logoObjectKey: item.logoObjectKey,
                    dateFounded: item.dateFounded,
                    startupStage: item.startupStage,
                    description: item.description,
                    location: item.location,
                    revenueModel: item.revenueModel
                });
                break;
            case 'CONTACTS':
                startup.contacts = item.contacts;
                break;
            case 'INDUSTRIES':
                startup.industry = item.industries;
                break;
            case 'MILESTONES':
                startup.milestones = item.milestones;
                break;
            case 'FOUNDERS':
                startup.founders = item.founders;
                break;
        }
    });

    return startup;
}
