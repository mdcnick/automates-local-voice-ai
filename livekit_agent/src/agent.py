import logging
import os
from typing import Any

from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    RunContext,
    cli,
    function_tool,
)
from livekit.agents.llm import FallbackAdapter
from livekit.plugins import deepgram, openai, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")

load_dotenv(".env.local", override=True)
load_dotenv(".env.local")


def build_llm():
    raw = os.getenv("LLM_MODEL", "meta-llama/llama-3.3-70b-instruct:free")
    chain = [m.strip() for m in raw.split(",")]
    openrouter_llm = openai.LLM.with_openrouter(
        model=chain[0], fallback_models=chain[1:]
    )
    local_llm = openai.LLM(
        base_url=os.getenv("LOCAL_LLM_BASE_URL", "http://llama_cpp:11434/v1"),
        model=os.getenv("LOCAL_LLM_MODEL", "qwen3-4b"),
        api_key="no-key-needed",
    )
    return FallbackAdapter([openrouter_llm, local_llm])


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""You are a helpful voice AI assistant. The user is interacting with you via voice, even if you perceive the conversation as text.
            You eagerly assist users with their questions by providing information from your extensive knowledge.
            Your responses are concise, to the point, and without any complex formatting or punctuation including emojis, asterisks, or other symbols.
            You are curious, friendly, and have a sense of humor.""",
        )

    @function_tool()
    async def multiply_numbers(
        self,
        context: RunContext,
        number1: int,
        number2: int,
    ) -> dict[str, Any]:
        """Multiply two numbers.

        Args:
            number1: The first number to multiply.
            number2: The second number to multiply.
        """

        return f"The product of {number1} and {number2} is {number1 * number2}."


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session()
async def my_agent(ctx: JobContext):
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    deepgram_model = os.getenv("DEEPGRAM_STT_MODEL", "nova-3")
    deepgram_language = os.getenv("DEEPGRAM_LANGUAGE", "en")

    logger.info(
        "Starting agent with STT=deepgram model=%s language=%s LLM_MODEL=%s",
        deepgram_model,
        deepgram_language,
        os.getenv("LLM_MODEL", "meta-llama/llama-3.3-70b-instruct:free"),
    )

    stt = deepgram.STT(
        model=deepgram_model,
        language=deepgram_language,
    )

    session = AgentSession(
        stt=stt,
        llm=build_llm(),
        tts=openai.TTS(
            base_url="http://kokoro:8880/v1",
            # base_url="http://localhost:8880/v1", # uncomment for local testing
            model="kokoro",
            voice="af_nova",
            api_key="no-key-needed",
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    # Track whether a holding message has already been spoken for this error episode.
    # Reset when a terminal (unrecoverable) error fires so that a fresh episode
    # can speak the holding message again.
    _holding_spoken = False

    @session.on("error")
    def on_session_error(event) -> None:
        nonlocal _holding_spoken
        error = event.error
        recoverable = getattr(error, "recoverable", True)
        logger.error(
            "Session error (recoverable=%s source=%s): %s",
            recoverable,
            type(event.source).__name__,
            error,
        )
        if recoverable:
            if not _holding_spoken:
                _holding_spoken = True
                session.say("Hang on a sec.")
        else:
            # Terminal failure — reset flag so next episode can speak again
            _holding_spoken = False
            session.say("Sorry, I can't answer that right now.")

    await ctx.connect()

    await session.start(
        agent=Assistant(),
        room=ctx.room,
    )


if __name__ == "__main__":
    cli.run_app(server)
