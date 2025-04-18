import { util } from '@aws-appsync/utils';

export function request(ctx) {
    const createdAt = util.time.nowISO8601();
    const ksuid = util.autoKsuid();

    const {
        entityType,
        entityId,
        savedProfileId,
        savedProfileType
    } = ctx.args.input;

    return {
        operation: 'PutItem',
        key: util.dynamodb.toMapValues({
            hashKey: `${entityType}#${entityId}`,
            rangeKey: `${entityType}#SAVED_PROFILE#${savedProfileType}#${savedProfileId}`
        }),
        attributeValues: util.dynamodb.toMapValues({
            enablerId: entityType === 'ENABLER' ? entityId : null,
            startupId: entityType === 'STARTUP' ? entityId : null,
            entityType,
            savedProfileId,
            savedProfileType,
            createdAt,
            updatedAt: createdAt,
            GSI1PK: ksuid
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
        id: ctx.result.startupId || ctx.result.enablerId,
        message: `Profile saved successfully`,
        success: true
    };
}
