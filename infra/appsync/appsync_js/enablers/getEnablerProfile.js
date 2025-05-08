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

    const { items } = ctx.result;
    if (items.length === 0) {
        util.error("Enabler not found", "NotFound");
    }

    const { enablerId } = ctx.arguments;

    // Initialize the enabler object
    const enabler = {
        enablerId: enablerId,
    };

    const suggestions = [];

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
                    preferredBusinessModels: item.preferredBusinessModels,
                    createdAt: item.createdAt,
                    visibility: item.visibility,
                    updatedAt: item.updatedAt,
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

        if (item.rangeKey.startsWith('ENABLER#SUGGESTION')) {
            const suggestion = {
                suggestionId: item.suggestionId,
                role: item.role,
                name: item.name,
                logoObjectKey: item.logoObjectKey,
                dateFounded: item.dateFounded,
                industryFocus: item.industryFocus,
                description: item.description,
            }
            suggestions.push(suggestion);
        }
    });

    enabler.suggestions = suggestions;

    return enabler;
}
