from __future__ import annotations

from typing import Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from engine import Engine
    from entity import Entity


class Action:

    def __init__(self, entity: Entity) -> None:
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


class EscapeAction(Action):
    
    def perform(self) -> None:
        raise SystemExit()


class ActionWithDirection(Action):

    def __init__(self, entity: Entity, dx: int, dy: int) -> None:
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
    
    def perform(self) -> None:
        raise NotImplementedError


class BumpAction(ActionWithDirection):

    def perform(self) -> None:
        if self.blocking_entity:
            return MeleeAction(self.entity, self.dx, self.dy).perform()
        else:
            return MovementAction(self.entity, self.dx, self.dy).perform()


class MeleeAction(ActionWithDirection):

    def perform(self) -> None:
        target = self.blocking_entity

        if not target:
            # No entity to attack
            return
        
        print(f"You kick the {target.name}, much to it's annoyance!")


class MovementAction(ActionWithDirection):
    
    def perform(self) -> None:
        dest_x, dest_y = self.dest_xy

        if not self.engine.game_map.in_bounds(dest_x, dest_y):
            # Destination is out of bounds
            return
        
        if not self.engine.game_map.tiles["walkable"][dest_x, dest_y]:
            # Destination is blocked by a tile
            return
        
        if self.engine.game_map.get_blocking_entity_at_location(dest_x, dest_y):
            # Destination is blocked by an entity
            return
        
        self.entity.move(self.dx, self.dy)
