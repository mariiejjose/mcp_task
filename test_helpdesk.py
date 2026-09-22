import pytest
from mcp import Client
from helpdesk_server import mcp
import re

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

# @pytest.mark.anyio
# async def test_search_faq_returns_vpn_ans():
#     async with Client(mcp) as client:
#         result = await client.call_tool("search_faq", {"query": "VPN"},)

#         text = result.content[0].text

#         assert not result.is_error
#         assert "GlobalConnect" in text
#         assert "SSO" in text

# @pytest.mark.anyio
# async def test_create_ticket():
#     async with Client(mcp) as client:
#         result = await client.call_tool(
#             "create_ticket",
#             {
#                 "title": "Keyboard not working",
#                 "priority": "medium",
#                 "owner": "mj",
#             },
#         )
#         text = result.content[0].text

#         assert not result.is_error
#         assert "Created ticket" in text
#         assert "Keyboard not working" in text
#         assert "mj" in text

@pytest.mark.anyio
async def test_close_ticket():
    async with Client(mcp) as client:

        create_result = await client.call_tool(
            "create_ticket",
            {
                "title": "Mouse not working",
                "priority": "low",
                "owner": "mj",
            },
        )
        create_text = create_result.content[0].text

        ticket_id = int(re.search(r"#(\d+)", create_text).group(1))
        close_result = await client.call_tool(
            "close_ticket",
            {
                "ticket_id": ticket_id,
                "resolution": "Mouse was replaced",
            },
        )
        close_text = close_result.content[0].text

        assert not close_result.is_error
        assert "Closed ticket" in close_text
        assert "Mouse was replaced" in close_text

