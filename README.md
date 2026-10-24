# Rocket Wagon

Factorio 2.1 mod (Space Age optional). A cargo wagon with two rocket launchers on its roof. They work like rocket
turrets, also while the train is moving, and reload from rockets in the wagon's cargo.

- Put rockets into the wagon (10 slots). Each launcher keeps 10 rockets loaded.
- With Space Age the launchers are rocket turrets (range 36). Without Space Age they have the stats of the rocket
  launcher (range 36).
- Minimum range 8, so explosions stay clear of the train. Combine with a machine gun wagon for close defence.
- The launchers turn and unfold faster than a rocket turret, so they can hit targets while passing.
- Rocket damage and shooting speed research applies as usual. Wagon quality carries over to the launchers.
- Works on elevated rails. The launchers need no heating on Aquilo.
- Unlocked by the technology "Rocket wagon" (after railway and rocket turret, or rocketry without Space Age).

## How it works

Factorio has no turrets on rolling stock. Each wagon gets two hidden turrets (not selectable, not attackable,
no collision). While the wagon moves, the script teleports them along with it every tick; standing wagons cost
nothing per tick. Every 30 ticks the launchers are topped up from the wagon. Mining the wagon returns the loaded rockets.
## Tests

    python tests/run.py                 # headless, with Space Age
    python tests/run.py --no-space-age
    python tests/ingame.py              # opens a game window: build, mine, ghost revive, blueprint
    python tests/shots.py               # opens a game window briefly, writes previews/shots/*.png

## Release

    python tools/package.py             # dist/<name>_<version>.zip
    python tools/publish.py publish     # first release (needs FACTORIO_API_KEY)
    python tools/publish.py upload      # later releases
