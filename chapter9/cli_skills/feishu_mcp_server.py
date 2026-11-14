"""Expose Feishu document search as a read-only stdio MCP tool."""

from __future__ import annotations

from typing import Annotated

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import BaseModel, Field

from check_feishu_access import workspace_environment
from feishu_search import search_documents


server = MCPServer("workshop-feishu")


class Document(BaseModel):
    title: str
    url: str
    doc_type: str


class SearchPage(BaseModel):
    documents: list[Document]
    has_more: bool
    next_page_token: str | None


@server.tool(structured_output=True, annotations=ToolAnnotations(
    readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=True,
))
def search_feishu_documents(
    query: Annotated[str, Field(max_length=30)] = "",
    page_size: Annotated[int, Field(ge=1, le=20)] = 10,
    page_token: str | None = None,
) -> SearchPage:
    """Search Docx, legacy docs and Wiki visible to the authorized Feishu user."""
    try:
        page = search_documents(query, page_size, page_token, workspace_environment())
    except RuntimeError as error:
        raise ToolError(str(error)) from None
    return SearchPage.model_validate(page)


if __name__ == "__main__":
    server.run(transport="stdio")
