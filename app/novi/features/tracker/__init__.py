"""Tracker feature: job applications board. Registers its routes and tab with the app."""
from novi import registry

from .api import ROUTES

registry.register(
    "tracker",
    ROUTES,
    {
        "label": "Tracker",
        "script": "tracker.js",
        "style": "tracker.css",
        # line icon: an SVG path d on a 20x20 grid (a briefcase)
        "icon": "M3 6.5h14v10H3zM7.5 6.5V5a1.5 1.5 0 0 1 1.5-1.5h2A1.5 1.5 0 0 1 12.5 5v1.5M3 11h14",
        "group": "work",
    },
)
