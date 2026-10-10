from google.adk.tools import ToolContext
from google.adk.tools.base_tool import BaseTool
import json
from typing import Any, Dict, Optional


ALLOWED_USERS = {"vishal", "alice"}


def check_data_access(
    tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext
) -> Optional[Dict]:
    """Runs just before each tool call.

    Access control: if the caller (session.user_id) is in ALLOWED_USERS the
    tool call proceeds; otherwise it is short-circuited with an "access denied"
    response and the tool never runs.
    """
    tool_name = tool.name
    print(f"[Callback] Before tool call for '{tool_name}'")
    print(f"[Callback] Original args: {args}")

    # Identify the caller.
    session = tool_context._invocation_context.session
    try:
        user_id = session.user_id.strip().lower()
    except AttributeError:
        user_id = ""

    # Gate the call on the allow-list.
    if user_id not in ALLOWED_USERS:
        print(f"[Callback] Access denied for user '{user_id}' (not in allow-list)")
        return {
            "status": "DENIED",
            "message": f"Access denied: user '{user_id or 'unknown'}' is not "
                       "authorized to use this tool.",
        }

    print(f"[Callback] Access granted for user '{user_id}'")

    print("[Callback] Proceeding with normal tool call")
    return None


USER_DEPARTMENT_MAP = {
    "vishal": "Finance",
    "alice": "Sales",
    "user": "Engineering",
}

def filter_data(
    tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext, tool_response: Any
) -> Optional[Dict]:
    """Filter the rows returned by `execute_sql` to the caller's department.

    The inbuilt `execute_sql` returns a dict like:
        {"status": "SUCCESS", "rows": [ {col: val, ...}, ... ], ...}
    We keep the envelope but replace `rows` with the department-filtered subset.
    """
    print("*******After tool working *********************")
    if tool.name != "execute_sql":
        return None

    # 1. Resolve the caller's department.
    session = tool_context._invocation_context.session
    try:
        user_id = session.user_id.strip().lower()
    except AttributeError:
        user_id = "user"

    department = USER_DEPARTMENT_MAP.get(user_id)
    if not department:
        return {
            "status": "DENIED",
            "rows": [],
            "message": "You do not have access to department-specific data.",
        }

    # 2. Normalise the response into a dict envelope + list of rows.
    response = tool_response
    print(f"*****Bigquery Output*******" ,response)
    if isinstance(response, str):
        try:
            response = json.loads(response)
        except json.JSONDecodeError:
            return {
                "status": "ERROR",
                "rows": [],
                "message": "Tool response was malformed and could not be filtered.",
            }

    if isinstance(response, dict):
        rows = response.get("rows", [])
        envelope = dict(response)
    elif isinstance(response, list):
        rows = response
        envelope = {"status": "SUCCESS"}
    else:
        return None

    # 3. Filter rows by department (case-insensitive).
    filtered = [
        row
        for row in rows
        if isinstance(row, dict)
        and str(row.get("department", "")).strip().lower() == department.lower()
    ]

    print(
        f"[Callback] After execute_sql: user='{user_id}' dept='{department}' "
        f"{len(rows)} -> {len(filtered)} rows"
    )

    envelope["rows"] = filtered
    if not filtered:
        envelope["message"] = f"No data found for department: {department}."
    return envelope