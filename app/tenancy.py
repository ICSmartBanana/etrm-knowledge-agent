"""The tenant context: the only way to say which client a request belongs to.

A TenantContext is built from the authenticated session (the simulated login in the UI, or the
session header in the API). No code path builds one from the user's question text.
"""

from __future__ import annotations

from dataclasses import dataclass

CLIENT_TENANTS = ("clan_a", "clan_b", "clan_c")
SHARED_TENANT = "consultancy"

DISPLAY_NAMES = {
    "clan_a": "Clan A (Aldermoor Energy)",
    "clan_b": "Clan B (Brightwater Refined Products)",
    "clan_c": "Clan C (Cerrado Agri Commodities)",
}


class UnknownTenantError(ValueError):
    pass


@dataclass(frozen=True)
class TenantContext:
    tenant_id: str

    def __post_init__(self) -> None:
        if self.tenant_id not in CLIENT_TENANTS:
            raise UnknownTenantError(f"not a client tenant: {self.tenant_id!r}")

    @property
    def visible_tenants(self) -> tuple[str, str]:
        return (self.tenant_id, SHARED_TENANT)
