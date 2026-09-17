import sys
from datetime import date
from typing import Literal

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations


mcp = MCPServer(
    "helpdesk",
    instructions="IT helpdesk tools for employees."
)
FAQ = {
    "vpn": (
        "Install GlobalConnect from the Software Center, "
        "then sign in with your SSO account."
    ),
    "password": (
        "Reset it at https://sso.example.com/reset "
        "(12+ characters)."
    ),
    "printer": (
        "Printers are named by floor, e.g. PRN-3F. "
        "Add them from Settings > Printers."
    ),
    "wifi": (
        "Join 'Corp-Secure' and sign in with your SSO account."
    ),
}


TICKETS = {
    1001: {
        "title": "Laptop fan is loud",
        "priority": "low",
        "status": "open",
        "owner": "sara",
        "created": "2026-09-01",
    },
    1002: {
        "title": "Cannot access shared drive",
        "priority": "high",
        "status": "in_progress",
        "owner": "omar",
        "created": "2026-09-03",
    },
}
Status = Literal["open", "in_progress", "closed", "all"]


def log(msg: str) -> None:
    print(f"[helpdesk] {msg}", file=sys.stderr)

@mcp.tool(annotations=ToolAnnotations(read_only_hint=True))
def search_faq(query: str) -> str:
    """Search the IT FAQ. Use this first for how-to questions (VPN, password, printer, wifi)."""

    hits = [text for topic, text in FAQ.items() if topic in query.lower()]

    return "\n".join(hits) or "No FAQ entry found. Consider a ticket."

@mcp.tool()
def create_ticket(title: str, owner: str, priority: Literal["low", "medium", "high"] = "medium", ) -> str:
    """Open a new IT support ticket for an employee. Returns the ticket ID."""

    if not title.strip():
        raise ToolError("title should not be empty.")

    if not owner.strip():
        raise ToolError("owner should not be empty.")

    ticket_id = max(TICKETS) + 1

    TICKETS[ticket_id] = {
        "title": title,
        "priority": priority,
        "status": "open",
        "owner": owner,
        "created": date.today().isoformat(),
    }
    log(f"created ticket {ticket_id}")

    return (f"Created ticket #{ticket_id} ({priority}) for {owner}: {title}"
    )

@mcp.tool(annotations=ToolAnnotations(read_only_hint=True))
def get_ticket(ticket_id: int) -> str:
    """Get the details and current status of one ticket by its ID."""

    ticket = TICKETS.get(ticket_id)

    if ticket is None:
        raise ToolError(f"Ticket #{ticket_id} does not exist")

    return f"#{ticket_id}: " + ", ".join(f"{key}={value}" for key, value in ticket.items())

@mcp.tool(annotations=ToolAnnotations(destructive_hint=True))
def close_ticket(ticket_id: int, resolution: str) -> str:
    """Close an IT support ticket and store the resolution."""

    ticket = TICKETS.get(ticket_id)
    if ticket is None:
        raise ToolError(f"Ticket #{ticket_id} does not exist.")

    if ticket["status"] == "closed":
        return f"Ticket #{ticket_id} is already closed."

    ticket["status"] = "closed"
    ticket["resolution"] = resolution

    log(f"closed ticket {ticket_id}")

    return f"Closed ticket #{ticket_id}: {resolution}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True))
def list_tickets(status: Status = "all") -> str:
    """List tickets, optionally filtered by status."""

    rows = [
        f"#{ticket_id} [{ticket['status']}] "
        f"{ticket['title']} (owner: {ticket['owner']})"
        for ticket_id, ticket in TICKETS.items()
        if status == "all" or ticket["status"] == status
    ]
    return "\n".join(rows) or "No tickets match."

@mcp.tool(annotations=ToolAnnotations(read_only_hint=True))
def my_ticket(owner: str) -> str:
    """List all IT support tickets for one employee."""

    rows = [f"#{ticket_id} [{ticket['status']}] {ticket['title']} (priority: {ticket['priority']})"
            for ticket_id, ticket in TICKETS.items() if ticket["owner"].lower() == owner.lower()
        ]
    return "\n".join(rows) or f"No tickets found for {owner}."

@mcp.resource("helpdesk://policies")
def policies() -> str:
    """Helpdesk service-level policy."""

    return (
        "High priority: reply within 4h."
        "Medium: 1 business day."
        "Low: 3 business days."
    )

@mcp.resource("helpdesk://tickets/{ticket_id}")
def ticket_resource(ticket_id: str) -> str:
    """Return one helpdesk ticket as a read-only resource."""

    ticket_id_int = int(ticket_id)
    ticket = TICKETS.get(ticket_id_int)

    if ticket is None:
        return f"Ticket #{ticket_id_int} does not exist"

    return f"#{ticket_id_int}: " + ", ".join(f"{key}={value}" for key, value in ticket.items())

@mcp.prompt()
def triage(problem: str) -> str:
    """Create a prompt for handling a new IT problem report."""

    return (f"Help traige this IT problem: {problem}. "  
            "First check whether the FAQ can answer it. "
            "If the FAQ does not solve the prob, gather the employee name. "
            "and sugget creatinf a support ticket.")

if __name__ == "__main__":
    mcp.run(transport="stdio")

#Command: C:/Users/mjmarie/Desktop/MCP_TASK/.venv/Scripts/python.exe
#Arguments: C:/Users/mjmarie/Desktop/MCP_TASK/helpdesk_server.py