"""Test the home resource routes."""

import pytest
from fastapi import status


@pytest.mark.integration()
class TestHomeRoutes:
    """Test the home resource routes."""

    @pytest.mark.asyncio()
    async def test_root_json(self, client) -> None:
        """Test the root route returns a JSON response."""
        response = await client.get("/")
        assert response.status_code == status.HTTP_200_OK


    @pytest.mark.asyncio()
    async def test_root_html(self, client) -> None:
        """Test the root route returns an HTML response when requested."""
        response = await client.get("/")
        assert response.status_code == status.HTTP_200_OK