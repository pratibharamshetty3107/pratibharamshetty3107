from google.adk.agents.llm_agent import Agent
from google.adk.tools import ToolContext
from google.genai import types


async def save_note(note: str, tool_context: ToolContext) -> str:
    """Save a text note as an ADK artifact."""

    artifact = types.Part.from_text(
        text=note
    )

    version = await tool_context.save_artifact(
        filename="my_note.txt",
        artifact=artifact,
    )

    return f"Note saved as an artifact. Version: {version}"


async def read_note(tool_context: ToolContext) -> str:
    """Read the saved note artifact."""

    artifact = await tool_context.load_artifact(
        filename="my_note.txt"
    )

    if artifact is None:
        return "No note artifact found."

    return artifact.text


root_agent = Agent(
    model='gemini-3.5-flash',
    name='root_agent',
    description='A helpful assistant for user which saves notes and help user to remind data in notes.',
    instruction="""
    A helpful assistant for user which saves notes and help user to remind data in notes.
    For saving notes use tool save note and reading note use read note tools.
    """,
    tools=[save_note, read_note]
)
