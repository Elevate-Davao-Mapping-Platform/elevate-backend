import { util } from '@aws-appsync/utils';

export function request(ctx) {
    const enablerId = util.autoId();
    const createdAt = util.time.nowISO8601();
    const ksuid = util.autoKsuid();

    const tableName = ctx.env.TABLE_NAME;

    const batchPutItems = [];

    // Metadata item
    batchPutItems.push(
        util.dynamodb.toMapValues({
            hashKey: `ENABLER#${enablerId}`,
            rangeKey: 'ENABLER#METADATA',
            enablerId,
            enablerName: ctx.args.input.enablerName,
            email: ctx.args.input.email,
            logoObjectKey: ctx.args.input.logoObjectKey,
            dateFounded: ctx.args.input.dateFounded,
            organizationType: ctx.args.input.organizationType,
            description: ctx.args.input.description,
            location: ctx.args.input.location,
            industryFocus: ctx.args.input.industryFocus,
            supportType: ctx.args.input.supportType,
            fundingStageFocus: ctx.args.input.fundingStageFocus,
            investmentAmount: ctx.args.input.investmentAmount,
            startupStagePreference: ctx.args.input.startupStagePreference,
            preferredBusinessModels: ctx.args.input.preferredBusinessModels,
            GSI1PK: ksuid,
            createdAt,
        })
    );

    // Add contacts if provided
    if (ctx.args.input.contacts) {
        const contacts = Array.isArray(ctx.args.input.contacts) ? ctx.args.input.contacts : [ctx.args.input.contacts];
        batchPutItems.push(
            util.dynamodb.toMapValues({
                hashKey: `ENABLER#${enablerId}`,
                rangeKey: 'ENABLER#CONTACTS',
                enablerId,
                contacts: contacts,
                GSI1PK: ksuid,
                createdAt,
            })
        );
    }

    // Add investment criteria if provided
    if (ctx.args.input.investmentCriteria) {
        batchPutItems.push(
            util.dynamodb.toMapValues({
                hashKey: `ENABLER#${enablerId}`,
                rangeKey: 'ENABLER#INVESTMENT_CRITERIA',
                enablerId,
                investmentCriteria: ctx.args.input.investmentCriteria,
                GSI1PK: ksuid,
                createdAt,
            })
        );
    }

    // Add portfolio if provided
    if (ctx.args.input.portfolio) {
        batchPutItems.push(
            util.dynamodb.toMapValues({
                hashKey: `ENABLER#${enablerId}`,
                rangeKey: 'ENABLER#PORTFOLIO',
                enablerId,
                portfolio: ctx.args.input.portfolio,
                GSI1PK: ksuid,
                createdAt,
            })
        );
    }

    return {
        operation: 'BatchPutItem',
        tables: {
            [tableName]: batchPutItems,
        }
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
            success: false
        };
    }

    // Extract enablerId from the hashKey of the first item
    const { enablerId } = ctx.result.data[tableName][0];

    return {
        id: enablerId,
        message: "Enabler successfully created",
        success: true
    };
}
