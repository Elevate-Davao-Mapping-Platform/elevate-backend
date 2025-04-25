import { util } from '@aws-appsync/utils';

export function request(ctx) {
    const tableName = ctx.env.TABLE_NAME;
    const { enablerId } = ctx.args;
    const transactItems = [];

    // Metadata update
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
        enablerName: '#enablerName'
    };

    const forSuggestionGenerationChangedFields =[
        'description',
        'industryFocus',
        'supportType',
        'fundingStageFocus',
        'investmentAmount',
        'startupStagePreference',
        'preferredBusinessModels',
        'investmentCriteria',
        'portfolio'
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
            hashKey: `ENABLER#${enablerId}`,
            rangeKey: 'ENABLER#METADATA'
        }),
        update: {
            expression: `SET ${updateExpression.join(', ')}`,
            expressionValues: util.dynamodb.toMapValues(expressionValues),
            expressionNames: expressionNames
        },
        condition: { expression: "attribute_exists(hashKey)" }
    });

    // Update contacts if provided
    if (ctx.args.input.contacts) {
        transactItems.push({
            table: tableName,
            operation: 'UpdateItem',
            key: util.dynamodb.toMapValues({
                hashKey: `ENABLER#${enablerId}`,
                rangeKey: 'ENABLER#CONTACTS'
            }),
            update: {
                expression: 'SET contacts = :contacts',
                expressionValues: util.dynamodb.toMapValues({
                    ':contacts': ctx.args.input.contacts
                }),
            },
            condition: { expression: "attribute_exists(hashKey)" }
        });
    }

    // Update investment criteria if provided
    if (ctx.args.input.investmentCriteria) {
        transactItems.push({
            table: tableName,
            operation: 'UpdateItem',
            key: util.dynamodb.toMapValues({
                hashKey: `ENABLER#${enablerId}`,
                rangeKey: 'ENABLER#INVESTMENT_CRITERIA'
            }),
            update: {
                expression: 'SET investmentCriteria = :investmentCriteria',
                expressionValues: util.dynamodb.toMapValues({
                    ':investmentCriteria': ctx.args.input.investmentCriteria
                }),
            },
            condition: { expression: "attribute_exists(hashKey)" }
        });
    }

    // Update portfolio if provided
    if (ctx.args.input.portfolio) {
        transactItems.push({
            table: tableName,
            operation: 'UpdateItem',
            key: util.dynamodb.toMapValues({
                hashKey: `ENABLER#${enablerId}`,
                rangeKey: 'ENABLER#PORTFOLIO'
            }),
            update: {
                expression: 'SET portfolio = :portfolio',
                expressionValues: util.dynamodb.toMapValues({
                    ':portfolio': ctx.args.input.portfolio
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

    const { enablerId } = ctx.args;

    return {
        id: enablerId,
        message: "Enabler successfully updated",
        success: true
    };
}
