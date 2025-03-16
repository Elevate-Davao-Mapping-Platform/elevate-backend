import { util } from '@aws-appsync/utils';

export function request(ctx) {
    const startupId = ctx.args.input.startupId || util.autoId();
    const tableName = 'elevate-dev-EntityTable';
    const transactItems = [];
    const createdAt = util.time.nowISO8601()
    const ksuid = util.autoKsuid()

    // Metadata item - use UpdateItem if startupId exists, otherwise PutItem
    if (ctx.args.input.startupId) {
        const updateExpression = [];
        const expressionValues = {};
        const expressionNames = {};

        // Build update expression for each field if provided
        const fields = {
            email: '#email',
            logoObjectKey: '#logo',
            dateFounded: '#founded',
            startupStage: '#stage',
            description: '#desc',
            revenueModel: '#revenue',
            location: '#loc',
            industries: '#industries'
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
                hashKey: `STARTUP#${startupId}`,
                rangeKey: 'STARTUP#METADATA'
            }),
            update: {
                expression: `SET ${updateExpression.join(', ')}`,
                expressionValues: util.dynamodb.toMapValues(expressionValues),
                expressionNames: expressionNames
            }
        });
    } else {
        // New startup - use PutItem
        transactItems.push({
            table: tableName,
            operation: 'PutItem',
            key: util.dynamodb.toMapValues({
                hashKey: `STARTUP#${startupId}`,
                rangeKey: 'STARTUP#METADATA'
            }),
            attributeValues: util.dynamodb.toMapValues({
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
                createdAt
            })
        });
    }

    // Add new founders if provided
    if (ctx.args.input.founders) {
        const founders = Array.isArray(ctx.args.input.founders) ? ctx.args.input.founders : [ctx.args.input.founders];
        transactItems.push({
            table: tableName,
            operation: 'PutItem',
            key: util.dynamodb.toMapValues({
                hashKey: `STARTUP#${startupId}`,
                rangeKey: 'STARTUP#FOUNDERS'
            }),
            attributeValues: util.dynamodb.toMapValues({
                startupId,
                founders: founders,
                GSI1PK: ksuid,
                ...(ctx.args.input.startupId && { createdAt })
            })
        });
    }

    // Add similar blocks for contacts, milestones, and industries
    if (ctx.args.input.contacts) {
        const contacts = Array.isArray(ctx.args.input.contacts) ? ctx.args.input.contacts : [ctx.args.input.contacts];
        transactItems.push({
            table: tableName,
            operation: 'PutItem',
            key: util.dynamodb.toMapValues({
                hashKey: `STARTUP#${startupId}`,
                rangeKey: 'STARTUP#CONTACTS'
            }),
            attributeValues: util.dynamodb.toMapValues({
                startupId,
                contacts: contacts,
                GSI1PK: ksuid,
                ...(ctx.args.input.startupId && { createdAt })
            })
        });
    }

    // Add similar blocks for milestones and industries
    if (ctx.args.input.milestones) {
        const milestones = Array.isArray(ctx.args.input.milestones) ? ctx.args.input.milestones : [ctx.args.input.milestones];
        transactItems.push({
            table: tableName,
            operation: 'PutItem',
            key: util.dynamodb.toMapValues({
                hashKey: `STARTUP#${startupId}`,
                rangeKey: 'STARTUP#MILESTONES'
            }),
            attributeValues: util.dynamodb.toMapValues({
                startupId,
                milestones: milestones,
                GSI1PK: ksuid,
                ...(ctx.args.input.startupId && { createdAt })
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

    // Extract startupId from the hashKey of the first item
    // hashKey format is "STARTUP#<startupId>"
    const startupId = ctx.result.keys[0].hashKey.split('#')[1];

    return {
        id: startupId,
        message: ctx.args.input.startupId ?
            "Startup successfully updated" :
            "Startup successfully created",
        success: true
    };
}
