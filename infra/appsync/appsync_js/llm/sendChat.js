import { util } from "@aws-appsync/utils";

export function request(ctx) {
    const entryId = util.autoId();
    const arguments_payload = {
        ...ctx.args.input,
        entryId,
    };

    ctx.stash.entryId = entryId;

    return {
        operation: "Invoke",
        invocationType: "Event",
        payload: { field: "sendChat", arguments: arguments_payload },
    };
}

export function response(ctx) {
    return {
        id: ctx.stash.entryId,
        message: "Chat sent successfully",
        success: true,
    };
}
