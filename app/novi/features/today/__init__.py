"""Today feature: to-do list, customisable habits, streaks and the contributions grid."""
from novi import registry

from .api import ROUTES

registry.register(
    "today",
    ROUTES,
    {
        "label": "Today",
        "script": "today.js",
        "style": "today.css",
        # line icon: four squares on a 20x20 grid
        "icon": "M3 3h6v6H3zM11 3h6v6h-6zM3 11h6v6H3zM11 11h6v6h-6z",
        "group": None,  # its own top-level item, not in a group
    },
)
