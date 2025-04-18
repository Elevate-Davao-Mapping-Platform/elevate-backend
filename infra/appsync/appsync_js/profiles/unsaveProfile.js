import { util } from '@aws-appsync/utils';

export function request(ctx) {
    const {
        entityType,
        entityId,
        savedProfileId,
        savedProfileType
    } = ctx.args.input;

    return {
        operation: 'DeleteItem',
        key: util.dynamodb.toMapValues({
            hashKey: `${entityType}#${entityId}`,
            rangeKey: `${entityType}#SAVED_PROFILE#${savedProfileType}#${savedProfileId}`
        }),
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

    return {
        id: ctx.args.input.entityId,
        message: `Profile unsaved successfully`,
        success: true
    };
}
