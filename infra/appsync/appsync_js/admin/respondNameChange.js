export function request(ctx) {
  const { requestId, isApproved, entityId, entityType } = ctx.args.input;

  console.log('respondNameChange', ctx.args.input)

  return {
    requestId,
    isApproved,
    entityId,
    entityType
  };
}

export function response(ctx) {
  return ctx.result;
}
