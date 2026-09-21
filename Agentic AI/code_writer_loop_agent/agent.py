from google.adk.agents import LoopAgent, LlmAgent, SequentialAgent
from google.adk.tools.tool_context import ToolContext
from google.adk.agents.callback_context import CallbackContext

# --- Constants ---
GEMINI_MODEL = "gemini-3.5-flash"

# --- State Keys ---
# STATE_CURRENT_CODE = "current_code"
# STATE_CRITICISM = "criticism"
# Define the exact phrase the Reviewer should use to signal completion
COMPLETION_PHRASE = "No major issues found."

# --- Tool Definition ---
def exit_loop(tool_context: ToolContext):
    """Call this function ONLY when the critique indicates no further changes are needed, signaling the iterative process should end."""
    print(f"  [Tool Call] exit_loop triggered by {tool_context.agent_name}")
    tool_context.actions.escalate = True
    tool_context.actions.skip_summarization = True
    # Return empty dict as tools should typically return JSON-serializable output
    return {}

# --- Before Agent Callback ---
def update_initial_topic_state(callback_context: CallbackContext):
    """Ensure 'initial_topic' is set in state before pipeline starts."""
    callback_context.state['initial_topic'] = callback_context.state.get(
        'initial_topic',
        'a Python function that reads a CSV file and returns the rows as dicts'
    )

# --- Agent Definitions ---

# STEP 1: Initial Code Writer Agent (Runs ONCE at the beginning)
initial_writer_agent = LlmAgent(
    name="InitialWriterAgent",
    model=GEMINI_MODEL,
    include_contents='none',
    instruction=f"""
    You are a Python Developer tasked with writing a first implementation.
    Write a *very basic* first version (just the minimal working code).
    Keep it plain and minimal - do NOT add error handling, type hints or docstrings yet.
    Requirement: {{initial_topic}}

    Output *only* the Python code inside a single ```python code block.
    Do not add introductions or explanations.
    """,
    description="Writes the initial code implementation based on the requirement.",
    output_key="code"
)

# STEP 2a: Code Reviewer Agent (Inside the Refinement Loop)
critic_agent_in_loop = LlmAgent(
    name="CodeReviewerAgent",
    model=GEMINI_MODEL,
    include_contents='none',
    instruction=f"""
    You are a Senior Python Code Reviewer reviewing an implementation.

    **Code to Review:**
    ```
    {{code}}
    ```

    **Completion Criteria (ALL must be met):**
    1. Has a docstring explaining what the function does
    2. Handles at least one failure case (missing file, bad input, empty data)
    3. Uses type hints on the function signature
    4. No obvious bugs and no leftover TODOs or placeholder code

    **Task:**
    Check the code against the criteria above.

    IF any criteria is NOT met, provide specific, actionable feedback on what to fix.
    Output *only* the review comments.

    IF all criteria ARE met, output *exactly* this phrase and nothing else:
    {COMPLETION_PHRASE}
    """,
    description="Reviews the current code, providing critique if clear improvements are needed, otherwise signals completion.",
    output_key="review_comment"
)

# STEP 2b: Refiner/Exiter Agent (Inside the Refinement Loop)
refiner_agent_in_loop = LlmAgent(
    name="RefinerAgent",
    model=GEMINI_MODEL,
    # Relies solely on state via placeholders
    include_contents='none',
    instruction=f"""
    You are a Python Developer fixing code based on review comments OR exiting the process.
    **Current Code:**
    ```
    {{code}}
    ```
    **Review Comments:**
    {{review_comment}}

    **Task:**
    Analyze the 'Review Comments'.
    IF the review comments are *exactly* "{COMPLETION_PHRASE}":
    You MUST call the 'exit_loop' function. Do not output any text.
    ELSE (the review contains actionable feedback):
    Carefully apply the fixes to improve the 'Current Code'.
    Output *only* the refined Python code inside a single ```python code block.

    Do not add explanations. Either output the refined code OR call the exit_loop function.
    """,
    description="Refines the code based on review comments, or calls exit_loop if the review indicates completion.",
    tools=[exit_loop], # Provide the exit_loop tool
    output_key="code" # Overwrites state['current_code'] with the refined version
)

# STEP 2: Refinement Loop Agent
refinement_loop = LoopAgent(
    name="RefinementLoop",
    # Agent order is crucial: Review first, then Refine/Exit
    sub_agents=[
        critic_agent_in_loop,
        refiner_agent_in_loop,
    ],
    max_iterations=5 # Limit loops
)

# STEP 3: Overall Sequential Pipeline
# For ADK tools compatibility, the root agent must be named `root_agent`
root_agent = SequentialAgent(
    name="IterativeCodingPipeline",
    sub_agents=[
        initial_writer_agent, # Run first to create initial code
        refinement_loop       # Then run the review/refine loop
    ],
    before_agent_callback=update_initial_topic_state, # set initial requirement in state
    description="Writes an initial code implementation and then iteratively refines it with code review using an exit tool."
)
