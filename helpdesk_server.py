import sys
from datetime import date
from typing import Literal

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations

import sqlite3


mcp = MCPServer(
    "helpdesk",
    instructions="IT helpdesk tools for employees."
)

DATABASE = "helpdesk.db"

def init_db():
    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets(
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            priority TEXT NOT NULL,
            status TEXT NOT NULL,
            owner TEXT NOT NULL,
            created TEXT NOT NULL,
            resolution TEXT
        )
    """)
    connection.commit()
    connection.close()

def insert_ticket_db():
    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()
    starter_tickets = [
        (
            1001,
            "Laptop fan is loud",
            "low",
            "open",
            "sara",
            "2026-09-01",
            None,
        ),
        (
            1002,
            "Cannot access shared drive",
            "high",
            "in_progress",
            "omar",
            "2026-09-03",
            None,
        ),
    ]
    cursor.executemany(
        """
        INSERT OR IGNORE INTO tickets
        (id, title, priority, status, owner, created, resolution)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        starter_tickets,
    )
    connection.commit()
    connection.close()

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

Status = Literal["open", "in_progress", "closed", "all"]


def log(msg: str) -> None:
    print(f"[helpdesk] {msg}", file=sys.stderr)

@mcp.tool(annotations=ToolAnnotations(read_only_hint=True))
def search_faq(query: str) -> str:
    """Search the IT FAQ. Use this first for how-to questions (VPN, password, printer, wifi)."""

    hits = [text for topic, text in FAQ.items() if topic in query.lower()]

    return "\n".join(hits) or "No FAQ entry found. Consider a ticket."

@mcp.tool()
def create_ticket(
    title: str,
    priority: Literal["low", "medium", "high"],
    owner: str,
) -> str:
    """Create a new IT support ticket."""

    if not title.strip():
        raise ToolError("Ticket title must not be empty")

    if not owner.strip():
        raise ToolError("Ticket owner must not be empty")

    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()
    cursor.execute(
        """
        INSERT INTO tickets
        (title, priority, status, owner, created, resolution)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            title.strip(),
            priority,
            "open",
            owner.strip(),
            date.today().isoformat(),
            None,
        ),
    )
    ticket_id = cursor.lastrowid
    connection.commit()
    connection.close()

    log(f"created ticket {ticket_id}")
    return (
        f"Created ticket #{ticket_id} "
        f"({priority}) for {owner}: {title}"
    )

@mcp.tool(annotations=ToolAnnotations(read_only_hint=True))
def get_ticket(ticket_id: int) -> str:
    """Get the details and current status of one ticket by its ID."""

    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute(
        "SELECT * FROM tickets WHERE id = ?",
        (ticket_id,),
    )
    ticket = cursor.fetchone()
    connection.close()

    if ticket is None:
        raise ToolError(f"Ticket #{ticket_id} does not exist")

    return(
        f"#{ticket['id']}: "
        f"title={ticket['title']}, "
        f"priority={ticket['priority']}, "
        f"status={ticket['status']}, "
        f"owner={ticket['owner']}, "
        f"created={ticket['created']}, "
        f"resolution={ticket['resolution']}"
    )


@mcp.tool(annotations=ToolAnnotations(destructive_hint=True))
def close_ticket(ticket_id: int, resolution: str) -> str:
    """Close an IT support ticket and store the resolution."""

    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    cursor.execute(
        "SELECT * FROM tickets WHERE id = ?",
        (ticket_id,),
    )
    ticket = cursor.fetchone()

    if ticket is None:
        connection.close()
        raise ToolError(f"Ticket #{ticket_id} does not exist")

    if ticket["status"] == "closed":
        connection.close()
        return f"Ticket #{ticket_id} is already closed."

    cursor.execute(
        """
        UPDATE tickets
        SET status = ?, resolution = ?
        WHERE id = ?
        """,
        (
            "closed",
            resolution,
            ticket_id,
        ),
    )
    connection.commit()
    connection.close()

    log(f"closed ticket {ticket_id}")
    return f"Closed ticket #{ticket_id}: {resolution}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True))
def list_tickets(status: Status = "all") -> str:
    """List helpdesk tickets, optionally filtered by status."""

    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    if status == "all":
        cursor.execute("SELECT * FROM tickets ORDER BY id")
    else:
        cursor.execute(
            "SELECT * FROM tickets WHERE status = ? ORDER BY id",
            (status,),
        )
    tickets = cursor.fetchall()
    connection.close()

    if not tickets:
        return "No tickets found."

    rows = [
        f"#{ticket['id']} [{ticket['status']}] "
        f"{ticket['title']} "
        f"(priority: {ticket['priority']}, owner: {ticket['owner']})"
        for ticket in tickets
    ]

    return "\n".join(rows)

@mcp.tool(annotations=ToolAnnotations(read_only_hint=True))
def my_tickets(owner: str) -> str:
    """List all IT support tickets for one employee."""

    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT * FROM tickets
        WHERE LOWER(owner) = LOWER(?)
        ORDER BY id
        """,
        (owner,),
    )
    tickets = cursor.fetchall()
    connection.close()

    if not tickets:
        return f"No tickets found for {owner}."

    rows = [
        f"#{ticket['id']} [{ticket['status']}] "
        f"{ticket['title']} "
        f"(priority: {ticket['priority']})"
        for ticket in tickets
    ]
    return "\n".join(rows)

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

    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    cursor.execute(
        "SELECT * FROM tickets WHERE id = ?",
        (ticket_id_int,),
    )
    ticket = cursor.fetchone()
    connection.close()

    if ticket is None:
        return f"Ticket #{ticket_id_int} does not exist"

    return (
        f"#{ticket['id']}: "
        f"title={ticket['title']}, "
        f"priority={ticket['priority']}, "
        f"status={ticket['status']}, "
        f"owner={ticket['owner']}, "
        f"created={ticket['created']}, "
        f"resolution={ticket['resolution']}"
    )

@mcp.prompt()
def triage(problem: str) -> str:
    """Create a prompt for handling a new IT problem report."""

    return (f"Help traige this IT problem: {problem}. "  
            "First check whether the FAQ can answer it. "
            "If the FAQ does not solve the prob, gather the employee name. "
            "and sugget creatinf a support ticket.")


if __name__ == "__main__":
    init_db()
    insert_ticket_db()
    mcp.run(transport="stdio")

#Command: C:/Users/mjmarie/Desktop/MCP_TASK/.venv/Scripts/python.exe
#Arguments: C:/Users/mjmarie/Desktop/MCP_TASK/helpdesk_server.py