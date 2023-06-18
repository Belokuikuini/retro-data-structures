"""
For checking which game is being parsed
"""
from __future__ import annotations
import typing
import uuid
from enum import Enum
from typing import Any, Callable

import construct
from construct.core import IfThenElse

from retro_data_structures import common_types

if typing.TYPE_CHECKING:
    from retro_data_structures.base_resource import AssetId


class Game(Enum):
    PRIME = 1
    ECHOES = 2
    CORRUPTION = 3
    PRIME_REMASTER = 10

    def __ge__(self, other):
        if self.__class__ is other.__class__:
            return self.value >= other.value
        return NotImplemented

    def __gt__(self, other):
        if self.__class__ is other.__class__:
            return self.value > other.value
        return NotImplemented

    def __le__(self, other):
        if self.__class__ is other.__class__:
            return self.value <= other.value
        return NotImplemented

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented

    @property
    def uses_asset_id_32(self):
        return self <= Game.ECHOES

    @property
    def uses_asset_id_64(self):
        return self == Game.CORRUPTION

    @property
    def uses_guid_as_asset_id(self):
        return self == Game.PRIME_REMASTER

    @property
    def uses_lzo(self):
        return self in {Game.ECHOES, Game.CORRUPTION}

    @property
    def invalid_asset_id(self) -> typing.Union[int, uuid.UUID]:
        if self.uses_asset_id_32:
            return (1 << 32) - 1
        elif self.uses_asset_id_64:
            return (1 << 64) - 1
        elif self.uses_guid_as_asset_id:
            return uuid.UUID(int=0)
        else:
            raise NotImplementedError()

    def is_valid_asset_id(self, asset_id: typing.Union[int, uuid.UUID]) -> bool:
        if self <= Game.ECHOES and asset_id == 0:
            return False
        return asset_id != self.invalid_asset_id
    
    @property
    def mlvl_dependencies_to_ignore(self) -> tuple[AssetId]:
        if self == Game.ECHOES:
            return (0x7b2ea5b1,)
        return ()


def get_current_game(ctx):
    result = ctx["_params"]["target_game"]
    if not isinstance(result, Game):
        raise ValueError(f"build/parse didn't set a valid target_game. Expected `Game`, got {result}")

    return result


def is_prime1(ctx):
    return get_current_game(ctx) == Game.PRIME


def is_prime2(ctx):
    return get_current_game(ctx) == Game.ECHOES


def is_prime3(ctx):
    return get_current_game(ctx) == Game.CORRUPTION


def current_game_at_most(target: Game) -> Callable[[Any], bool]:
    def result(ctx):
        return get_current_game(ctx) <= target

    return result


def current_game_at_least(target: Game) -> Callable[[Any], bool]:
    def result(ctx):
        return get_current_game(ctx) >= target

    return result


class CurrentGameCheck(IfThenElse):
    def __init__(self, target: Game, subcon1, subcon2):
        super().__init__(current_game_at_least(target), subcon1, subcon2)
        self.target_game = target

    def _emitparse(self, code: construct.CodeGen):
        code.append("from retro_data_structures import game_check")
        return "((%s) if (game_check.get_current_game(this) >= game_check.Game.%s) else (%s))" % (
            self.thensubcon._compileparse(code),
            self.target_game.name,
            self.elsesubcon._compileparse(code),
        )

    def _emitbuild(self, code: construct.CodeGen):
        code.append("from retro_data_structures import game_check")
        return f"(({self.thensubcon._compilebuild(code)}) if (game_check.get_current_game(this) >= game_check.Game.{self.target_game.name}) else ({self.elsesubcon._compilebuild(code)}))"


def current_game_at_least_else(target: Game, subcon1, subcon2) -> IfThenElse:
    return CurrentGameCheck(target, subcon1, subcon2)


def uses_asset_id_32(ctx):
    return get_current_game(ctx).uses_asset_id_32


def uses_lzo(ctx):
    return get_current_game(ctx).uses_lzo


AssetIdCorrect = IfThenElse(uses_asset_id_32, common_types.AssetId32, common_types.AssetId64)
ObjectTagCorrect = IfThenElse(uses_asset_id_32, common_types.ObjectTag_32, common_types.ObjectTag_64)
