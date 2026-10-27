"""Research scaffold for reinforcement-learning route policies.

This module is intentionally lightweight so the project remains runnable in a
student/demo environment. Replace the reward function and transition source
with a simulator such as SUMO when city-scale traces are available.
"""

from dataclasses import dataclass


@dataclass
class RouteState:
    eta: float
    congestion: float
    safety_risk: float
    fuel: float


def reward(state: RouteState) -> float:
    return -(0.55 * state.eta + 18 * state.congestion + 12 * state.safety_risk + 2.5 * state.fuel)

