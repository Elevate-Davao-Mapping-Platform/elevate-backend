import { util } from "@aws-appsync/utils";

export function request(ctx) {
    const startupId = util.autoId();
    const createdAt = util.time.nowISO8601();
    const ksuid = util.autoKsuid();

    const tableName = ctx.env.TABLE_NAME;

    const batchPutItems = [];

    batchPutItems.push(
        util.dynamodb.toMapValues({
            hashKey: `STARTUP#${startupId}`,
            rangeKey: "STARTUP#METADATA",
            startupId,
            startUpName: ctx.args.input.startUpName,
            email: ctx.args.input.email,
            logoObjectKey: ctx.args.input.logoObjectKey,
            dateFounded: ctx.args.input.dateFounded,
            startupStage: ctx.args.input.startupStage,
            description: ctx.args.input.description,
            revenueModel: ctx.args.input.revenueModel,
            location: ctx.args.input.location,
            industries: ctx.args.input.industries,
            GSI1PK: ksuid,
            createdAt,
        })
    );

    const founders = ctx.args.input.founders || [];
    batchPutItems.push(
        util.dynamodb.toMapValues({
            hashKey: `STARTUP#${startupId}`,
            rangeKey: "STARTUP#FOUNDERS",
            startupId,
            founders: founders,
            GSI1PK: ksuid,
            createdAt,
        })
    );

    const contacts = ctx.args.input.contacts || [];
    batchPutItems.push(
        util.dynamodb.toMapValues({
            hashKey: `STARTUP#${startupId}`,
            rangeKey: "STARTUP#CONTACTS",
            startupId,
            contacts: contacts,
            GSI1PK: ksuid,
            createdAt,
        })
    );

    const milestones = ctx.args.input.milestones || [];
    batchPutItems.push(
        util.dynamodb.toMapValues({
            hashKey: `STARTUP#${startupId}`,
            rangeKey: "STARTUP#MILESTONES",
            startupId,
            milestones: milestones,
            GSI1PK: ksuid,
            createdAt,
        })
    );

    return {
        operation: "BatchPutItem",
        tables: {
            [tableName]: batchPutItems,
        },
    };
}

/**
 * Handles the response from DynamoDB
 * @param {import('@aws-appsync/utils').Context} ctx the context
 * @returns {*} the inserted items
 */
export function response(ctx) {
    const tableName = ctx.env.TABLE_NAME;

    if (ctx.error) {
        return {
            id: null,
            message: ctx.error.message,
            success: false,
        };
    }

    // Extract startupId from the hashKey of the first item
    const startupId = ctx.result.data[tableName][0].startupId;

    return {
        id: startupId,
        message: "Startup successfully created",
        success: true,
    };
}
