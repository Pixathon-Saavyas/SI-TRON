from ai_engine import UAgentResponse, UAgentResponseType
from uagents import Agent, Context, Protocol, Model

reel_creation_proto = Protocol("ReelCreation")

class ReelCreation(Model):
    websiteUrl: str

@reel_creation_proto.on_message(model=ReelCreation, replies={UAgentResponse})
async def booking_handler(ctx: Context, sender: str, msg: ReelCreation):
    ctx.logger.info(f"Received booking request from {sender}")
    try:
        option = ctx.storage.get(msg.request_id)
        await ctx.send(
            sender,
            UAgentResponse(
                message=f"Thanks for choosing an option - {option[msg.user_response]}.",
                type=UAgentResponseType.FINAL,
                request_id=msg.request_id
            )
        )
    except Exception as exc:
        ctx.logger.error(exc)
        await ctx.send(
            sender,
            UAgentResponse(
                message=str(exc),
                type=UAgentResponseType.ERROR
            )
        )
