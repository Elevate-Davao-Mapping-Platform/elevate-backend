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
                ":hashKey": `ENABLER#${ctx.args.enablerId}`,
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
        util.error("Enabler not found", "NotFound");
    }

    const enablerId = ctx.arguments.enablerId;

    // Initialize the enabler object
    const enabler = {
        enablerId: enablerId,
    };

    // Process each item based on its rangeKey
    items.forEach(item => {
        switch (item.rangeKey) {
            case 'ENABLER#METADATA':
                Object.assign(enabler, {
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
                enabler.contacts = item.contacts;
                break;
            case 'ENABLER#INVESTMENT_CRITERIA':
                enabler.investmentCriteria = item.investmentCriteria;
                break;
            case 'ENABLER#PORTFOLIO':
                enabler.portfolio = item.portfolio;
                break;
        }
    });

    return enabler;
}
