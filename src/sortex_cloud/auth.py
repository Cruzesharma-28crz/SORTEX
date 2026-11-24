import secrets
from dataclasses import dataclass
from fastapi import Header, HTTPException
from sortex_cloud.config import get_settings
@dataclass(frozen=True)
class Principal:
    owner: str
    role: str
def require_roles(*roles: str):
    def dependency(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> Principal:
        if not x_api_key: raise HTTPException(status_code=401, detail="API key required")
        for key, identity in get_settings().api_keys.items():
            if secrets.compare_digest(x_api_key, key):
                role = identity.get("role", "")
                if role not in roles: raise HTTPException(status_code=403, detail="Insufficient role")
                return Principal(owner=identity.get("owner", "unknown"), role=role)
        raise HTTPException(status_code=401, detail="Invalid API key")
    return dependency
contributor = require_roles("contributor", "trainer", "admin")
trainer = require_roles("trainer", "admin")
admin = require_roles("admin")
device = require_roles("device", "admin")
