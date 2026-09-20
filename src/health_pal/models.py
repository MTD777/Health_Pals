"""Reminder definitions.

A reminder is just data: what to nudge about, how often, and which cheerful
line Biscuit says. Keeping these as simple immutable records (no behaviour)
makes the system easy to reason about and extend with new activities.
"""
from __future__ import annotations

from dataclasses import dataclass, field


# Mascot mood shown alongside a reminder. Mascots interpret these names.
MOOD_WAVE = "wave"
MOOD_STRETCH = "stretch"
MOOD_CHEER = "cheer"
MOOD_WALK = "walk"
MOOD_DRINK = "drink"
MOOD_SLEEPY_EYES = "eyes"


@dataclass(frozen=True)
class Reminder:
    """A single health nudge template."""

    id: str
    title: str
    emoji: str
    # A few message variants so Biscuit doesn't sound repetitive.
    messages: tuple[str, ...]
    default_interval_min: int
    mood: str = MOOD_WAVE
    # Roughly how long the activity takes, shown as a hint.
    duration_hint: str = ""
    # Whether this reminder is on out-of-the-box. A sensible starter set is on;
    # the more intense/situational ones are off until the user opts in.
    enabled_by_default: bool = True


# The built-in roster of gentle, purposeful nudges.
DEFAULT_REMINDERS: tuple[Reminder, ...] = (
    Reminder(
        id="stand_up",
        title="Stand up",
        emoji="🧍",
        messages=(
            "Time to stand and shake it out!",
            "Up we go — give those legs a stretch.",
            "{pal} says: unstick yourself from that chair!",
        ),
        default_interval_min=45,
        mood=MOOD_STRETCH,
        duration_hint="30 sec",
    ),
    Reminder(
        id="standing_desk",
        title="Raise your desk",
        emoji="🎚️",
        messages=(
            "Flip to standing mode for a while?",
            "Let's work standing for the next stretch.",
            "Desk up! Your back will thank you.",
        ),
        default_interval_min=60,
        mood=MOOD_CHEER,
        duration_hint="a while",
        enabled_by_default=False,
    ),
    Reminder(
        id="step_out",
        title="Step outside",
        emoji="🚶",
        messages=(
            "A little fresh air would be lovely.",
            "Let's take a quick walk together!",
            "Two-minute stroll? {pal}'s ready.",
        ),
        default_interval_min=120,
        mood=MOOD_WALK,
        duration_hint="2–5 min",
    ),
    Reminder(
        id="quick_workout",
        title="Mini workout",
        emoji="💪",
        messages=(
            "10 squats — you've got this!",
            "Quick burst of movement, let's go!",
            "A tiny workout keeps the zoomies away.",
        ),
        default_interval_min=90,
        mood=MOOD_CHEER,
        duration_hint="1 min",
    ),
    Reminder(
        id="situps",
        title="Sit-ups",
        emoji="🤸",
        messages=(
            "How about 10 sit-ups?",
            "Core time! A quick set of sit-ups.",
            "Down on the floor for a few sit-ups?",
        ),
        default_interval_min=150,
        mood=MOOD_CHEER,
        duration_hint="1 min",
        enabled_by_default=False,
    ),
    Reminder(
        id="jumping_jacks",
        title="Jumping jacks",
        emoji="⭐",
        messages=(
            "20 jumping jacks to wake up!",
            "Let's get the heart going — jumping jacks!",
            "Bounce with {pal}: jumping jacks time.",
        ),
        default_interval_min=100,
        mood=MOOD_CHEER,
        duration_hint="30 sec",
        enabled_by_default=False,
    ),
    Reminder(
        id="hydrate",
        title="Sip some water",
        emoji="💧",
        messages=(
            "Hydration break — take a sip!",
            "Water time! Keep that brain happy.",
            "A little water goes a long way — take a sip!",
        ),
        default_interval_min=45,
        mood=MOOD_DRINK,
        duration_hint="10 sec",
    ),
    Reminder(
        id="eye_rest",
        title="Rest your eyes",
        emoji="👀",
        messages=(
            "Look 20 feet away for 20 seconds.",
            "Give your eyes a little horizon break.",
            "20-20-20: gaze into the distance a moment.",
        ),
        default_interval_min=20,
        mood=MOOD_SLEEPY_EYES,
        duration_hint="20 sec",
    ),
    Reminder(
        id="posture",
        title="Posture check",
        emoji="🪑",
        messages=(
            "Shoulders back, chin up — reset that posture!",
            "Sit tall like a proud little bulldog.",
            "Uncurl the spine — posture check!",
        ),
        default_interval_min=30,
        mood=MOOD_STRETCH,
        duration_hint="5 sec",
    ),
    Reminder(
        id="stretch",
        title="Stretch break",
        emoji="🙆",
        messages=(
            "Reach for the sky and stretch it out.",
            "Neck rolls and a big stretch, please!",
            "Loosen up — stretch with {pal}.",
        ),
        default_interval_min=55,
        mood=MOOD_STRETCH,
        duration_hint="30 sec",
    ),
)


REMINDERS_BY_ID: dict[str, Reminder] = {r.id: r for r in DEFAULT_REMINDERS}


# --------------------------------------------------------------------------- #
# Custom (user-defined) reminders
# --------------------------------------------------------------------------- #
def custom_to_reminder(data: dict) -> Reminder:
    """Turn a stored custom-reminder dict into a Reminder record."""
    title = str(data.get("title", "Reminder")).strip() or "Reminder"
    emoji = str(data.get("emoji", "⭐")).strip() or "⭐"
    messages = data.get("messages")
    if not messages:
        messages = (f"Time for {title}!", f"{emoji} {title} — let's do it!")
    return Reminder(
        id=str(data["id"]),
        title=title,
        emoji=emoji,
        messages=tuple(messages),
        default_interval_min=int(data.get("interval_min", 30)),
        mood=MOOD_CHEER,
    )


def build_reminders(custom_list: list[dict] | None) -> tuple[Reminder, ...]:
    """All reminders = built-ins + any user-defined ones."""
    customs = tuple(custom_to_reminder(d) for d in (custom_list or []))
    return DEFAULT_REMINDERS + customs


def build_reminders_map(custom_list: list[dict] | None) -> dict[str, Reminder]:
    return {r.id: r for r in build_reminders(custom_list)}

