from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class Stats(BaseModel):
    str: int
    dex: int
    con: int
    int: int
    wis: int
    cha: int
    hp: int
    max_hp: int
    ac: int
    level: int
    xp: int

class Item(BaseModel):
    name: str
    quantity: int
    description: Optional[str] = None

class Character(BaseModel):
    name: str
    race: str
    class_name: str = Field(alias="class")
    stats: Stats
    inventory: List[Item]
    skills: List[str]
    background: str
    alignment: str

class Quest(BaseModel):
    id: str
    title: str
    description: str
    status: str  # "active", "completed", "failed"

class WorldState(BaseModel):
    current_location: str
    time_of_day: str
    turn_count: int
    active_quests: List[Quest]
    npcs_met: List[str]
    recent_events: List[str]
