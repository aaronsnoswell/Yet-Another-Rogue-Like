from __future__ import annotations
from components.inventory import Inventory

from typing import Optional, Tuple, TYPE_CHECKING

import color
import exceptions


if TYPE_CHECKING:
    from engine import Engine
    from entity import Actor, Entity, Item


class Action:

    def __init__(self, entity: Actor) -> None:
        super().__init__()
        self.entity = entity
    
    @property
    def engine(self) -> Engine:
        return self.entity.gamemap.engine
    
    def perform(self) -> None:
        """Perform this action with the objects needed to determine its scope
        
        `self.engine` is the scope this action is being performed in
        `self.entity` is the object performing the action

        This method must be overridden by Action subclasses
        """
        raise NotImplementedError()


class PickupAction(Action):
    """Pick up an item and add it to the inventory, if there is room"""

    def __init__(self, entity: Actor):
        super().__init__(entity)
    
    def perform(self) -> None:
        actor_location_x = self.entity.x
        actor_location_y = self.entity.y
        inventory = self.entity.inventory

        for item in self.engine.game_map.items:
            if actor_location_x == item.x and actor_location_y == item.y:
                if len(inventory.items) >= inventory.capacity:
                    raise exceptions.Impossible("Your inventory is full.")
                
                self.engine.game_map.entities.remove(item)
                item.parent = self.entity.inventory
                inventory.items.append(item)

                self.engine.message_log.add_message(
                    f"You picked up the {item.name}!"
                )
                return
        
        raise exceptions.Impossible("There is nothing here to pick up.")


class ItemAction(Action):

    def __init__(self, entity: Actor, item: Item, target_xy: Optional[Tuple[int, int]] = None) -> None:
        super().__init__(entity)
        self.item = item
        if not target_xy:
            target_xy = entity.x, entity.y
        self.target_xy = target_xy
    
    @property
    def target_actor(self) -> Optional[Actor]:
        """Return the actor at the destination of this action"""
        return self.engine.game_map.get_actor_at_location(*self.target_xy)
    
    def perform(self) -> None:
        """Invoke the item's ability"""
        self.item.consumable.activate(self)


class DropItem(ItemAction):

    def perform(self) -> None:
        self.entity.inventory.drop(self.item)


class WaitAction(Action):
    
    def perform(self) -> None:
        pass


class TakeStairsAction(Action):

    def perform(self) -> None:
        """Take the stairs, if any exist at an entity's location"""
        if (self.entity.x, self.entity.y) == self.engine.game_map.downstairs_location:
            self.engine.game_world.generate_floor()
            self.engine.message_log.add_message(
                "You descend the staircase.", color.descend
            )
        else:
            raise exceptions.Impossible("There are no stairs here.")


class ActionWithDirection(Action):

    def __init__(self, entity: Actor, dx: int, dy: int) -> None:
        super().__init__(entity)

        self.dx = dx
        self.dy = dy
    
    @property
    def dest_xy(self) -> Tuple[int, int]:
        """Returns the destination of this action"""
        return self.entity.x + self.dx, self.entity.y + self.dy
    
    @property
    def blocking_entity(self) -> Optional[Entity]:
        """Return the blocking entity at the destination of this action"""
        return self.engine.game_map.get_blocking_entity_at_location(*self.dest_xy)
    
    @property
    def target_actor(self) -> Optional[Actor]:
        """Return the actor at this actino's destination"""
        return self.engine.game_map.get_actor_at_location(*self.dest_xy)
    
    def perform(self) -> None:
        raise NotImplementedError


class BumpAction(ActionWithDirection):

    def perform(self) -> None:
        if self.target_actor:
            return MeleeAction(self.entity, self.dx, self.dy).perform()
        else:
            return MovementAction(self.entity, self.dx, self.dy).perform()


class MeleeAction(ActionWithDirection):

    def perform(self) -> None:
        target = self.target_actor

        if not target:
            # No entity to attack
            raise exceptions.Impossible("Nothing to attack.")
        
        damage = self.entity.fighter.power - target.fighter.defense

        attack_desc = f"{self.entity.name.capitalize()} attacks {target.name}"
        if self.entity is self.engine.player:
            attack_color = color.player_atk
        else:
            attack_color = color.enemy_atk

        if damage > 0:
            self.engine.message_log.add_message(
                f"{attack_desc} for {damage} hit points.",
                attack_color
            )
            target.fighter.hp -= damage
        else:
            self.engine.message_log.add_message(
                f"{attack_desc} but does no damage!",
                attack_color
            )


class MovementAction(ActionWithDirection):
    
    def perform(self) -> None:
        dest_x, dest_y = self.dest_xy

        if not self.engine.game_map.in_bounds(dest_x, dest_y):
            # Destination is out of bounds
            raise exceptions.Impossible("That way is blocked.")
        
        if not self.engine.game_map.tiles["walkable"][dest_x, dest_y]:
            # Destination is blocked by a tile
            raise exceptions.Impossible("That way is blocked.")
        
        blocking_entity = self.engine.game_map.get_blocking_entity_at_location(dest_x, dest_y)
        if blocking_entity:
            # Destination is blocked by an entity
            raise exceptions.Impossible(f"{blocking_entity.name} is in the way!")
        
        self.entity.move(self.dx, self.dy)
