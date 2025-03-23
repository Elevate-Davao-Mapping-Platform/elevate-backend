import { util } from "@aws-appsync/utils";

export function request(ctx) {
    const entryId = util.autoId();
    const chatTopicId = ctx.args.input.chatTopicId || util.autoId();
    const arguments_payload = {
        ...ctx.args.input,
        entryId,
    }
    if (!ctx.args.input.chatTopicId) {
        arguments_payload.chatTopicId = chatTopicId;
    }

    ctx.stash.entryId = entryId;
    ctx.stash.chatTopicId = chatTopicId;

    return {
        operation: "Invoke",
        invocationType: "Event",
        payload: { field: "sendChat", arguments: arguments_payload },
    };
}

export function response(ctx) {
    return {
        entryId: ctx.stash.entryId,
        message: "Chat sent successfully",
        success: true,
        chatTopicId: ctx.stash.chatTopicId,
    };
}
