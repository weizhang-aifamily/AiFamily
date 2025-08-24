from dataclasses import dataclass
from typing import List

@dataclass
class Dish:
    id: int
    name: str
    emoji: str
    default_portion_g: float
    max_servings: int
    calcium: float
    iron: float
    sodium: float
    purine: float
    kcal: float

@dataclass
class FamilyNeed:
    calcium_target: float
    iron_target: float
    sodium_limit: float
    purine_limit: float
    kcal_limit: float