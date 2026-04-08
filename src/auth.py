import os
from urllib.parse import urlparse

from mcp.server.auth.provider import AccessToken
from fastmcp.server.auth.providers.in_memory import InMemoryOAuthProvider
from fastmcp.server.auth.auth import ClientRegistrationOptions
from pydantic import AnyHttpUrl
from starlette.routing import Route


class TelegramOAuthProvider(InMemoryOAuthProvider):
    """
    OAuth 2.1 provider that also accepts a legacy static bearer token.

    - Claude connectors use the full OAuth 2.1 flow (DCR, PKCE, authorize, token).
    - Existing clients can continue using the static MCP_API_KEY.
    """

    def __init__(self, base_url: str):
        super().__init__(
            base_url=AnyHttpUrl(base_url),
            client_registration_options=ClientRegistrationOptions(
                enabled=True,
                valid_scopes=["admin"],
            ),
            required_scopes=["admin"],
        )

    async def verify_token(self, token: str) -> AccessToken | None:
        # First, check if it's a valid OAuth-issued token
        result = await super().verify_token(token)
        if result is not None:
            return result

        # Fall back to legacy static token for existing clients
        legacy_key = os.getenv("MCP_API_KEY")
        if legacy_key and token == legacy_key:
            return AccessToken(
                token=token,
                client_id="legacy-static-client",
                scopes=["admin"],
            )

        return None

    def get_routes(self, mcp_path: str | None = None) -> list[Route]:
        """
        Override to also register the RFC 8414 path-aware
        /.well-known/oauth-authorization-server{issuer_path} route.

        FastMCP only registers the non-path-aware version; Claude connectors
        need the path-aware variant when the server is behind a reverse proxy
        at a sub-path (e.g. /telegram).
        """
        routes = super().get_routes(mcp_path)

        if self.issuer_url:
            parsed = urlparse(str(self.issuer_url))
            issuer_path = parsed.path.rstrip("/")

            if issuer_path and issuer_path != "/":
                # Find the default well-known route and duplicate it with the path-aware URL
                for route in routes:
                    if (
                        isinstance(route, Route)
                        and route.path == "/.well-known/oauth-authorization-server"
                    ):
                        routes.append(
                            Route(
                                f"/.well-known/oauth-authorization-server{issuer_path}",
                                endpoint=route.endpoint,
                                methods=route.methods,
                            )
                        )
                        break

        return routes
