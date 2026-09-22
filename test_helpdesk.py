import pytest
from mcp import Client
from helpdesk_server import mcp

# @pytest.mark.anyio
# async def test_lists_expected_tools():
#     async with Client(mcp) as client:
#         names = {t.name for t in (await client.list_tools()).tools}
#         assert {"search_faq", "create_ticket", "get_ticket", "list_tickets"} <= names

# @pytest.mark.anyio
# async def test_unknown_ticket_is_a_tool_error():
#     async with Client(mcp) as client:
#         result = await client.call_tool("get_ticket", {"ticket_id": 9999})
#         assert result.is_error
#         assert "does not exist" in result.content[0].text



