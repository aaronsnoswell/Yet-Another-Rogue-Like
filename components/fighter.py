from __future__ import annotations

from typing import TYPE_CHECKING

import entity_factories

from render_order import RenderOrder
import color
from components.base_component import BaseComponent


if TYPE_CHECKING:
    from entity import Actor


class Fighter(BaseComponent):

    parent: Actor

    def __init__(self, hp: int, defense: int, power: int) -> None:
        self.max_hp = hp
        self._hp = hp
        self.defense = defense
        self.power = power
    
    @property
    def hp(self) -> int:
        return self._hp
    
    @hp.setter
    def hp(self, value: int) -> None:
        self._hp = max(0, min(value, self.max_hp))
        if self._hp == 0 and self.parent.ai:
            self.die()
    
    def die(self) -> None:
        if self.engine.player is self.parent:
            death_message = "You died!"
            death_message_color = color.player_die
        else:
            death_message = f"{self.parent.name} is dead!"
            death_message_color = color.enemy_die
        
        remains = entity_factories.remains_of.spawn(
            self.engine.game_map,
            self.parent.x,
            self.parent.y
        )
        remains.name = f"Remains of {self.parent.name}"
        remains.created_time = self.engine.world_age
        self.engine.game_map.entities.remove(self.parent)

        self.engine.message_log.add_message(death_message, death_message_color)
    
    def heal(self, amount: int) -> int:
        if self.hp == self.max_hp:
            return 0
         
        new_hp_value = min(self.hp + amount, self.max_hp)
        amount_recovered = new_hp_value - self.hp
        self.hp = new_hp_value
        return amount_recovered
    
    def take_damage(self, amount: int) -> None:
        self.hp -= amount
        return amount


