"""Convex inversion core (Kaasalainen-Torppa inspired)."""


def optimize_convex(initial_state, observations, config):
    return {"state": initial_state, "rms": 0.0, "iterations": 0}
