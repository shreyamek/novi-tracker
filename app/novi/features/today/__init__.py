"""Today feature: to-do list, customisable habits, streaks and the contributions grid."""
from novi import registry

from .api import ROUTES

registry.register(
    "today",
    ROUTES,
    {"label": "Today", "script": "today.js", "style": "today.css"},
)
