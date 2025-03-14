import { util } from "@aws-appsync/utils";

/**
 * Queries DynamoDB table for chat topics
 * @param {import('@aws-appsync/utils').Context} ctx the context
 * @returns {import('@aws-appsync/utils').DynamoDBQueryRequest} the request
 */
export function request(ctx) {
    return {
        operation: "Query",
        query: {
            expression: "hashKey = :hashKey",
            expressionValues: util.dynamodb.toMapValues({
                ":hashKey": `ChatTopic#${ctx.args.userId}`,
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
    return ctx.result.items;
}
