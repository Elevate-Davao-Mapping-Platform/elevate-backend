import { util } from '@aws-appsync/utils';

export function request(ctx) {
    const enablerId = ctx.args.input.enablerId || util.autoId();
    const tableName = 'elevate-dev-EntityTable';
    const transactItems = [];
    const createdAt = util.time.nowISO8601()
    const ksuid = util.autoKsuid()

    // Metadata item - use UpdateItem if enablerId exists, otherwise PutItem
    if (ctx.args.input.enablerId) {
        const updateExpression = [];
        const expressionValues = {};
        const expressionNames = {};

        // Build update expression for each field if provided
        const fields = {
            email: '#email',
            logoObjectKey: '#logo',
            dateFounded: '#founded',
            organizationType: '#orgType',
            description: '#desc',
            location: '#loc',
            industryFocus: '#industryFocus',
            supportType: '#supportType',
            fundingStageFocus: '#fundingStageFocus',
            investmentAmount: '#invAmount',
            startupStagePreference: '#stagePrefs',
            preferredBusinessModels: '#bizModels',
        };

        for (const [field, placeholder] of Object.entries(fields)) {
            if (ctx.args.input[field] !== undefined) {
                updateExpression.push(`${placeholder} = :${field}`);
                expressionValues[`:${field}`] = ctx.args.input[field];
                expressionNames[placeholder] = field;
            }
        }

        transactItems.push({
            table: tableName,
            operation: 'UpdateItem',
            key: util.dynamodb.toMapValues({
                hashKey: `ENABLER#${enablerId}`,
                rangeKey: 'ENABLER#METADATA'
            }),
            update: {
                expression: `SET ${updateExpression.join(', ')}`,
                expressionValues: util.dynamodb.toMapValues(expressionValues),
                expressionNames: expressionNames
            }
        });
    }

    else {
        // New enabler - use PutItem
        transactItems.push({
            table: tableName,
            operation: 'PutItem',
            key: util.dynamodb.toMapValues({
                hashKey: `ENABLER#${enablerId}`,
                rangeKey: 'ENABLER#METADATA'
            }),
            attributeValues: util.dynamodb.toMapValues({
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
        });
    }

    // Add contacts if provided
    if (ctx.args.input.contacts) {
        const contacts = Array.isArray(ctx.args.input.contacts) ? ctx.args.input.contacts : [ctx.args.input.contacts];
        transactItems.push({
            table: tableName,
            operation: 'PutItem',
            key: util.dynamodb.toMapValues({
                hashKey: `ENABLER#${enablerId}`,
                rangeKey: 'ENABLER#CONTACTS'
            }),
            attributeValues: util.dynamodb.toMapValues({
                enablerId,
                contacts: contacts,
                GSI1PK: ksuid,
                ...(ctx.args.input.enablerId && { createdAt })
            })
        });
    }

    // Add investment criteria if provided
    if (ctx.args.input.investmentCriteria) {
        transactItems.push({
            table: tableName,
            operation: 'PutItem',
            key: util.dynamodb.toMapValues({
                hashKey: `ENABLER#${enablerId}`,
                rangeKey: 'ENABLER#INVESTMENT_CRITERIA'
            }),
            attributeValues: util.dynamodb.toMapValues({
                enablerId,
                investmentCriteria: ctx.args.input.investmentCriteria,
                GSI1PK: ksuid,
                ...(ctx.args.input.enablerId && { createdAt })
            })
        });
    }

    // Add portfolio if provided
    if (ctx.args.input.portfolio) {
        transactItems.push({
            table: tableName,
            operation: 'PutItem',
            key: util.dynamodb.toMapValues({
                hashKey: `ENABLER#${enablerId}`,
                rangeKey: 'ENABLER#PORTFOLIO'
            }),
            attributeValues: util.dynamodb.toMapValues({
                enablerId,
                portfolio: ctx.args.input.portfolio,
                GSI1PK: ksuid,
                ...(ctx.args.input.enablerId && { createdAt })
            })
        });
    }

    return {
        operation: 'TransactWriteItems',
        transactItems: transactItems
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
            startupId: null,
            message: ctx.error.message,
            success: false
        };
    }

    // Extract enablerId from the hashKey of the first item
    const enablerId = ctx.result.keys[0].hashKey.split('#')[1];

    return {
        id: enablerId,
        message: ctx.args.input.enablerId ?
            "Enabler successfully updated" :
            "Enabler successfully created",
        success: true
    };
}
