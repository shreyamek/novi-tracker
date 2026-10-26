"""Tracker feature: job applications board. Registers its routes and tab with the app."""
from novi import registry

from .api import ROUTES

registry.register(
    "tracker",
    ROUTES,
    {"label": "Tracker", "script": "tracker.js", "style": "tracker.css"},
)
