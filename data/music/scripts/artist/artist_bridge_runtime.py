from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import importlib.util
from pathlib import Path
import sys
from types import ModuleType
from typing import Any, Mapping


BRIDGE_PATH = (
    Path(__file__).resolve().parents[1]
    / "bridge"
    / "artist_bridge.py"
)


@lru_cache(maxsize=1)
def _load_bridge_module() -> ModuleType:
    if not BRIDGE_PATH.exists():
        raise FileNotFoundError(
            f"Artist bridge module is missing: {BRIDGE_PATH}"
        )

    module_name = "_defending_sisyphus_artist_bridge"

    specification = importlib.util.spec_from_file_location(
        module_name,
        BRIDGE_PATH,
    )

    if (
        specification is None
        or specification.loader is None
    ):
        raise ImportError(
            f"Unable to load artist bridge: {BRIDGE_PATH}"
        )

    module = importlib.util.module_from_spec(specification)
    sys.modules[module_name] = module
    specification.loader.exec_module(module)

    if not callable(getattr(module, "bridge_artist", None)):
        raise AttributeError(
            "Artist bridge module does not expose bridge_artist()."
        )

    return module


def build_artist_bridge(
    artist_name: Any,
) -> dict[str, Any]:
    module = _load_bridge_module()

    bridge = module.bridge_artist(
        str(artist_name or "").strip()
    )

    if not isinstance(bridge, Mapping):
        raise TypeError(
            "Artist bridge response must be a mapping."
        )

    return deepcopy(dict(bridge))


def comparative_standing_from_bridge(
    bridge: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    if not isinstance(bridge, Mapping):
        return None

    live = bridge.get("live")

    if not isinstance(live, Mapping):
        return None

    comparative_standing = live.get(
        "comparativeStanding"
    )

    if not isinstance(comparative_standing, Mapping):
        return None

    return deepcopy(dict(comparative_standing))
