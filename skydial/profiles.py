"""Window-profile store. Profiles are data; switching never touches code."""

from __future__ import annotations

from .models import Profile


class ProfileError(Exception):
    """Raised when a requested profile doesn't exist."""


class ProfileStore:
    def __init__(self, profiles: list[Profile], active_id: str):
        if not profiles:
            raise ValueError("At least one profile is required")
        self._profiles: dict[str, Profile] = {p.id: p for p in profiles}
        if active_id not in self._profiles:
            active_id = profiles[0].id
        self._active_id = active_id

    @classmethod
    def from_config(cls, cfg: dict) -> "ProfileStore":
        profiles = [Profile(**p) for p in cfg.get("profiles", [])]
        return cls(profiles, cfg.get("active_profile", profiles[0].id if profiles else ""))

    def list(self) -> list[Profile]:
        return list(self._profiles.values())

    def get(self, profile_id: str) -> Profile:
        try:
            return self._profiles[profile_id]
        except KeyError as exc:
            raise ProfileError(f"Unknown profile: {profile_id!r}") from exc

    @property
    def active(self) -> Profile:
        return self._profiles[self._active_id]

    def set_active(self, profile_id: str) -> Profile:
        if profile_id not in self._profiles:
            raise ProfileError(f"Unknown profile: {profile_id!r}")
        self._active_id = profile_id
        return self.active
