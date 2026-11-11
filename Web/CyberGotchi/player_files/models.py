from dataclasses import dataclass

XP_PER_ACTION = 10
XP_PER_LEVEL = 100
MAX_LEVEL = 100
COOLDOWN_SECONDS = 300

@dataclass
class Pet:
    pet_id: str
    name: str = "BLOOP"
    xp: int = 0
    level: int = 1
    last_action: float = 0.0

    def gain_xp(self) -> None:
        self.xp += XP_PER_ACTION
        self.level = min(MAX_LEVEL, 1 + self.xp // XP_PER_LEVEL)

    def public_view(self, now: float) -> dict:
        return {
            "name": self.name,
            "stage": self.level,
            "progress": self.xp % XP_PER_LEVEL,
            "progress_max": XP_PER_LEVEL,
            "cooldown_remaining": max(0, int(self.last_action + COOLDOWN_SECONDS - now + 0.999)),
        }
