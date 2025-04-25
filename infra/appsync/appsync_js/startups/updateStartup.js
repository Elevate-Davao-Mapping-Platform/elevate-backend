import { util } from '@aws-appsync/utils';

export function request(ctx) {
    const tableName = ctx.env.TABLE_NAME;

    const transactItems = [];
    const { startupId } = ctx.args;

    const updateExpression = [];
    const expressionValues = {};
    const expressionNames = {};

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

    const forSuggestionGenerationChangedFields =[
        'description',
        'startupStage',
        'revenueModel',
        'location',
        'industries',
        'founders',
        'milestones',
    ]
    const forSuggestionGenerationChanged = forSuggestionGenerationChangedFields.some(field => ctx.args.input[field] !== undefined);
    updateExpression.push('#forSuggestionGeneration = :forSuggestionGeneration');
    expressionValues[`:forSuggestionGeneration`] = forSuggestionGenerationChanged;
    expressionNames[`#forSuggestionGeneration`] = 'forSuggestionGeneration';

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
        },
        condition: { expression: "attribute_exists(hashKey)" }

    });

    // Add new founders if provided
    if (ctx.args.input.founders) {
        transactItems.push({
            table: tableName,
            operation: 'UpdateItem',
            key: util.dynamodb.toMapValues({
                hashKey: `STARTUP#${startupId}`,
                rangeKey: 'STARTUP#FOUNDERS'
            }),
            update: {
                expression: `SET founders = :founders`,
                expressionValues: util.dynamodb.toMapValues({
                    ':founders': ctx.args.input.founders
                }),
            },
            condition: { expression: "attribute_exists(hashKey)" }
        });
    }

    // Add similar blocks for contacts, milestones, and industries
    if (ctx.args.input.contacts) {
        transactItems.push({
            table: tableName,
            operation: 'UpdateItem',
            key: util.dynamodb.toMapValues({
                hashKey: `STARTUP#${startupId}`,
                rangeKey: 'STARTUP#CONTACTS'
            }),
            update: {
                expression: `SET contacts = :contacts`,
                expressionValues: util.dynamodb.toMapValues({
                    ':contacts': ctx.args.input.contacts
                }),
            },
            condition: { expression: "attribute_exists(hashKey)" }
        });
    }

    // Add similar blocks for milestones and industries
    if (ctx.args.input.milestones) {
        transactItems.push({
            table: tableName,
            operation: 'UpdateItem',
            key: util.dynamodb.toMapValues({
                hashKey: `STARTUP#${startupId}`,
                rangeKey: 'STARTUP#MILESTONES'
            }),
            update: {
                expression: `SET milestones = :milestones`,
                expressionValues: util.dynamodb.toMapValues({
                    ':milestones': ctx.args.input.milestones
                }),
            },
            condition: { expression: "attribute_exists(hashKey)" }
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
            id: null,
            message: ctx.error.message,
            success: false
        };
    }

    const { startupId } = ctx.args;

    return {
        id: startupId,
        message: "Startup successfully updated",
        success: true
    };
}
