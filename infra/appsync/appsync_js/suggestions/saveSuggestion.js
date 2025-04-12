import { util } from '@aws-appsync/utils';

export function request(ctx) {
    const { entityType, entityId, matchPairId, matchPairType } = ctx.args.input;

    return {
        operation: 'UpdateItem',
        key: util.dynamodb.toMapValues({
            hashKey: `${entityType}#${entityId}`,
            rangeKey: `${entityType}#SUGGESTION#${matchPairType}#${matchPairId}`
        }),
        update: {
            expression: `SET isSaved = :isSaved`,
            expressionValues: util.dynamodb.toMapValues({
                ':isSaved': true
            })
        }
    };
}


/**
 * Handles the response from DynamoDB
 * @param {import('@aws-appsync/utils').Context} ctx the context
 * @returns {*} the inserted items
 */
export function response(ctx) {
    if (ctx.error) {
        return {
            id: null,
            message: ctx.error.message,
            success: false
        };
    }

    const { suggestionId } = ctx.result;

    return {
        id: suggestionId,
        message: "Suggestion successfully saved",
        success: true
    };
}
