"""Armoured turret wagons: machine gun (mg), flamethrower (flame) and rocket (rocket).

Run:  blender -b --factory-startup -P tools/blender/wagon.py -- <variant> <out_dir> [frames...]
Frames are 0..127, frame i shows orientation i/256 (back equals front).
The wheels are not modelled: Factorio draws its standard train wheels on top.
The turret heads are not modelled either: the game draws the vanilla turret heads
on top of the barbettes (round armoured mounts) modelled here.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import rig  # noqa: E402

# Wagon runs along Y, front (orientation 0) pointing north (+Y). Units are tiles.
HALF_LEN = 2.7  # hull
HALF_W = 0.98
SILL = 0.80  # top of the underframe
SKIRT_LOW = 0.6  # armour skirt bottom edge, above the wheels
BOGIE_Y = 2.0
END_Y = 3.2  # headstock
DECK = 1.45  # deck of the armoured hull (mg, rocket)

# Turret mounts (along Y), barbette radius, barbette top height. Keep the mounts in sync with config.lua.
VARIANTS = {
    "mg": {"mounts": (-1.9, 0.0, 1.9), "radius": 0.42, "top": DECK + 0.22},
    "flame": {"mounts": (-1.5, 1.5), "radius": 0.5, "top": 2.3},
    "rocket": {"mounts": (-1.5, 1.5), "radius": 0.66, "top": DECK + 0.2},
}


def materials():
    return {
        "paint": rig.material("paint", (0.27, 0.29, 0.22), roughness=0.55, grime=0.45, scale=2.5, bump=0.12, rust=0.75),
        "paint_worn": rig.material("paint_worn", (0.17, 0.17, 0.14), roughness=0.75, grime=0.55, scale=4, bump=0.3, rust=0.9),
        "armour": rig.material("armour", (0.25, 0.26, 0.21), roughness=0.6, grime=0.5, scale=3, bump=0.2, rust=0.6),
        "deck": rig.material("deck", (0.15, 0.155, 0.13), roughness=0.8, metallic=0.0, grime=0.55, scale=6, bump=0.4, rust=0.5),
        "steel": rig.material("steel", (0.24, 0.24, 0.25), roughness=0.35, metallic=0.75, grime=0.4, rust=0.35),
        "dark": rig.material("dark", (0.06, 0.06, 0.065), roughness=0.5, metallic=0.5, grime=0.3, rust=0.3),
        "sill": rig.material("sill", (0.42, 0.27, 0.08), roughness=0.55, grime=0.5, scale=4, rust=0.5),
        "rust": rig.material("rust", (0.28, 0.14, 0.06), roughness=0.85, grime=0.5, scale=8, bump=0.35),
        "rail": rig.material("rail", (0.72, 0.72, 0.70), roughness=0.3, metallic=0.85, grime=0.25),
        "rivet": rig.material("rivet", (0.30, 0.30, 0.31), roughness=0.3, metallic=0.8, grime=0.1),
        "crate": rig.material("crate", (0.3, 0.33, 0.2), roughness=0.7, grime=0.5, scale=5, bump=0.25, rust=0.3),
        "wood": rig.material("wood", (0.36, 0.25, 0.14), roughness=0.85, grime=0.5, scale=10, bump=0.4),
        "brass": rig.material("brass", (0.55, 0.42, 0.18), roughness=0.35, metallic=0.9, grime=0.3),
        "hazard": rig.material("hazard", (0.75, 0.55, 0.06), roughness=0.6, grime=0.5, scale=4, rust=0.4),
        "rocket": rig.material("rocket", (0.55, 0.12, 0.08), roughness=0.5, grime=0.3, scale=5),
        "tank": rig.material("tank", (0.24, 0.24, 0.2), roughness=0.5, grime=0.5, scale=2, bump=0.12, rust=0.8),
        "lamp": rig.material("lamp", (1.0, 0.7, 0.3), emission=(1.0, 0.55, 0.15)),
        "slit": rig.material("slit", (0.01, 0.01, 0.01), roughness=0.9),
    }


def rivet_row(name, start, end, count, m, radius=0.018, axis="x"):
    for k in range(count):
        t = k / (count - 1)
        p = tuple(start[i] + t * (end[i] - start[i]) for i in range(3))
        d = {"x": (0.012, 0, 0), "y": (0, 0.012, 0), "z": (0, 0, 0.012)}[axis]
        rig.cylinder(f"{name}_{k}", (p[0] - d[0], p[1] - d[1], p[2] - d[2]), (p[0] + d[0], p[1] + d[1], p[2] + d[2]),
                     radius, m["rivet"], verts=8)


def rivet_ring(name, center, radius, count, m):
    for k in range(count):
        a = 2 * math.pi * k / count
        x, y = center[0] + math.cos(a) * radius, center[1] + math.sin(a) * radius
        rig.cylinder(f"{name}_{k}", (x, y, center[2] - 0.01), (x, y, center[2] + 0.012), 0.017, m["rivet"], verts=8)


def solid(obj, thickness=0.04):
    mod = obj.modifiers.new("solid", "SOLIDIFY")
    mod.thickness = thickness
    mod.offset = -1
    mod.use_rim = True
    bevel = obj.modifiers.new("bevel", "BEVEL")
    bevel.width = 0.012
    bevel.segments = 2
    bevel.limit_method = "ANGLE"
    return obj


# ---------------------------------------------------------------- shared parts

def underframe(m):
    rig.box("centre_sill", (0, 0, SILL - 0.1), (0.3, 2 * END_Y, 0.2), m["dark"])
    for sx in (-1, 1):
        rig.box(f"side_sill{sx}", (sx * 0.9, 0, SILL - 0.07), (0.08, 2 * END_Y - 0.2, 0.15), m["sill"])
        rig.box(f"side_sill_lip{sx}", (sx * 0.86, 0, SILL), (0.16, 2 * END_Y - 0.2, 0.03), m["sill"])
        rivet_row(f"sill_rivets{sx}", (sx * 0.945, -2.9, SILL - 0.07), (sx * 0.945, 2.9, SILL - 0.07), 28, m, radius=0.014)
    for sy in (-1, 1):
        rig.box(f"bolster{sy}", (0, sy * BOGIE_Y, SILL - 0.12), (1.85, 0.3, 0.16), m["dark"])
        rig.box(f"bolster_plate{sy}", (0, sy * BOGIE_Y, SILL - 0.03), (1.6, 0.36, 0.02), m["steel"])
    rig.cylinder("brake_cyl", (0.3, -0.5, 0.62), (0.3, 0.1, 0.62), 0.11, m["dark"])
    rig.cylinder("reservoir", (-0.3, -0.2, 0.62), (-0.3, 0.6, 0.62), 0.1, m["steel"])


def ends(m, ladder_top):
    """End platforms with buffers, couplers, railings and a ladder up to ladder_top."""
    for sy in (-1, 1):
        rig.box(f"platform{sy}", (0, sy * (END_Y - 0.25), SILL - 0.02), (1.9, 0.5, 0.05), m["steel"])
        for k in range(4):
            rig.box(f"tread{sy}{k}", (0, sy * (END_Y - 0.44 + k * 0.1), SILL + 0.008), (1.8, 0.02, 0.01), m["dark"], bevel=0)
        rig.box(f"headstock{sy}", (0, sy * END_Y, SILL - 0.1), (1.94, 0.1, 0.24), m["sill"])
        # hazard stripes on the headstock
        for k in range(6):
            rig.box(f"stripe{sy}{k}", (-0.75 + k * 0.3, sy * (END_Y + 0.052), SILL - 0.1), (0.12, 0.01, 0.2), m["hazard"],
                    bevel=0, rotation=(0, math.radians(35), 0))
        for sx in (-1, 1):
            rig.cylinder(f"buffer_case{sy}{sx}", (sx * 0.58, sy * END_Y, SILL - 0.1), (sx * 0.58, sy * (END_Y + 0.14), SILL - 0.1), 0.075, m["dark"])
            rig.cylinder(f"buffer_head{sy}{sx}", (sx * 0.58, sy * (END_Y + 0.14), SILL - 0.1), (sx * 0.58, sy * (END_Y + 0.18), SILL - 0.1), 0.11, m["steel"], verts=20)
            rig.tube_path(f"railing{sy}{sx}", [
                (sx * 0.92, sy * (HALF_LEN + 0.05), SILL), (sx * 0.92, sy * (HALF_LEN + 0.05), SILL + 0.55),
                (sx * 0.92, sy * (END_Y - 0.06), SILL + 0.55), (sx * 0.92, sy * (END_Y - 0.06), SILL),
            ], 0.02, m["rail"])
            rig.box(f"lamp{sy}{sx}", (sx * 0.8, sy * (END_Y + 0.05), SILL + 0.04), (0.08, 0.04, 0.07), m["lamp"], bevel=0)
            rig.box(f"lamp_case{sy}{sx}", (sx * 0.8, sy * (END_Y + 0.02), SILL + 0.04), (0.11, 0.04, 0.1), m["dark"])
        rig.box(f"coupler{sy}", (0, sy * (END_Y + 0.12), SILL - 0.18), (0.18, 0.26, 0.12), m["dark"])
        rig.box(f"coupler_knuckle{sy}", (0, sy * (END_Y + 0.26), SILL - 0.18), (0.26, 0.08, 0.14), m["steel"])
        # ladder up the end wall
        for sx in (-0.18, 0.18):
            rig.cylinder(f"ladder{sy}{sx}", (sx, sy * (HALF_LEN + 0.12), SILL), (sx, sy * (HALF_LEN + 0.12), ladder_top + 0.25), 0.017, m["rail"])
        rungs = max(3, int((ladder_top - SILL) / 0.16))
        for k in range(rungs):
            z = SILL + (k + 1) * (ladder_top + 0.2 - SILL) / (rungs + 1)
            rig.cylinder(f"rung{sy}{k}", (-0.18, sy * (HALF_LEN + 0.12), z), (0.18, sy * (HALF_LEN + 0.12), z), 0.013, m["rail"])
    rig.torus("brake_wheel", (0.55, -2.95, SILL + 0.4), 0.12, 0.016, m["dark"], rotation=(math.pi / 2, 0, 0))
    rig.cylinder("brake_spindle", (0.55, -2.95, SILL), (0.55, -2.95, SILL + 0.4), 0.015, m["dark"])


def skirts(m):
    """Sloped armour plates hanging down the sides, riveted, over the underframe."""
    for sx in (-1, 1):
        plate = rig.mesh(f"skirt{sx}", [
            (sx * (HALF_W + 0.1), -HALF_LEN, SKIRT_LOW), (sx * (HALF_W + 0.1), HALF_LEN, SKIRT_LOW),
            (sx * HALF_W, HALF_LEN, 1.15), (sx * HALF_W, -HALF_LEN, 1.15),
        ], [(0, 1, 2, 3)], m["armour"], mask=True)
        solid(plate, 0.05)
        rivet_row(f"skirt_rivets_low{sx}", (sx * (HALF_W + 0.12), -HALF_LEN + 0.1, SKIRT_LOW + 0.06),
                  (sx * (HALF_W + 0.12), HALF_LEN - 0.1, SKIRT_LOW + 0.06), 30, m, radius=0.015)
        rivet_row(f"skirt_rivets_high{sx}", (sx * (HALF_W + 0.025), -HALF_LEN + 0.1, 1.1),
                  (sx * (HALF_W + 0.025), HALF_LEN - 0.1, 1.1), 30, m, radius=0.015)
        # vertical plate seams
        for k in range(5):
            y = -HALF_LEN + (k + 1) * 2 * HALF_LEN / 6
            rig.box(f"skirt_seam{sx}{k}", (sx * (HALF_W + 0.07), y, (SKIRT_LOW + 1.15) / 2), (0.03, 0.05, 0.56), m["armour"],
                    mask=True, rotation=(0, sx * math.radians(-10), 0))


def hull(m, deck=DECK):
    """Armoured box on the skirts: riveted walls with vision slits and a tread-plate deck."""
    rig.box("hull", (0, 0, (1.1 + deck) / 2), (2 * HALF_W, 2 * HALF_LEN, deck - 1.1), m["armour"], mask=True)
    rig.box("deck", (0, 0, deck + 0.015), (2 * HALF_W - 0.06, 2 * HALF_LEN - 0.06, 0.03), m["deck"])
    for i in range(14):
        y = -HALF_LEN + 0.2 + i * (2 * HALF_LEN - 0.4) / 13
        rig.box(f"deck_tread{i}", (0, y, deck + 0.033), (2 * HALF_W - 0.2, 0.025, 0.008), m["dark"], bevel=0)
    for sx in (-1, 1):
        rivet_row(f"hull_rivets{sx}", (sx * (HALF_W + 0.005), -HALF_LEN + 0.1, deck - 0.05),
                  (sx * (HALF_W + 0.005), HALF_LEN - 0.1, deck - 0.05), 30, m, radius=0.014)
        # vision slits with armoured hoods
        for y in (-2.0, -0.95, 0.95, 2.0):
            rig.box(f"slit{sx}{y}", (sx * (HALF_W + 0.005), y, deck - 0.17), (0.02, 0.32, 0.04), m["slit"], bevel=0)
            rig.box(f"hood{sx}{y}", (sx * (HALF_W + 0.04), y, deck - 0.12), (0.07, 0.4, 0.03), m["armour"], mask=True)
        # side door with hinges and a handle
        rig.box(f"door{sx}", (sx * (HALF_W + 0.012), 0, (1.15 + deck) / 2), (0.025, 0.6, deck - 1.2), m["paint_worn"])
        for z in (1.2, deck - 0.08):
            rig.cylinder(f"hinge{sx}{z}", (sx * (HALF_W + 0.03), -0.32, z - 0.04), (sx * (HALF_W + 0.03), -0.32, z + 0.04), 0.025, m["dark"])
        rig.box(f"handle{sx}", (sx * (HALF_W + 0.04), 0.22, 1.28), (0.03, 0.1, 0.03), m["steel"], bevel=0)
    for sy in (-1, 1):
        rivet_row(f"end_rivets{sy}", (-HALF_W + 0.1, sy * (HALF_LEN + 0.005), deck - 0.05),
                  (HALF_W - 0.1, sy * (HALF_LEN + 0.005), deck - 0.05), 12, m, radius=0.014, axis="y")


def deck_railing(m, deck, gaps=()):
    """Low railing round the deck edge; gaps (y ranges) leave room for barbettes."""
    for sx in (-1, 1):
        x = sx * (HALF_W - 0.04)
        posts = [-HALF_LEN + 0.08 + i * (2 * HALF_LEN - 0.16) / 9 for i in range(10)]
        for i, y in enumerate(posts):
            rig.cylinder(f"deck_post{sx}{i}", (x, y, deck), (x, y, deck + 0.3), 0.014, m["rail"], verts=8)
        rig.cylinder(f"deck_rail{sx}", (x, posts[0], deck + 0.3), (x, posts[-1], deck + 0.3), 0.018, m["rail"])
        rig.cylinder(f"deck_midrail{sx}", (x, posts[0], deck + 0.16), (x, posts[-1], deck + 0.16), 0.012, m["rail"])


def barbette(name, m, y, radius, base, top):
    """Round armoured turret mount: riveted drum with a race ring, the turret head sits on top."""
    rig.cylinder(f"{name}_drum", (0, y, base), (0, y, top - 0.04), radius, m["armour"], verts=40, mask=True)
    rig.cylinder(f"{name}_ring", (0, y, top - 0.04), (0, y, top), radius + 0.04, m["steel"], verts=40)
    rig.cylinder(f"{name}_race", (0, y, top), (0, y, top + 0.012), radius * 0.78, m["dark"], verts=40)
    rig.torus(f"{name}_lip", (0, y, base + 0.03), radius + 0.02, 0.025, m["armour"])
    rivet_ring(f"{name}_rivets", (0, y, top - 0.01), radius + 0.01, 20, m)
    for k in range(8):
        a = 2 * math.pi * k / 8 + math.pi / 8
        x0, y0 = math.cos(a) * (radius + 0.005), y + math.sin(a) * (radius + 0.005)
        rig.box(f"{name}_rib{k}", (x0, y0, (base + top) / 2), (0.05, 0.05, top - base - 0.06), m["armour"], mask=True,
                rotation=(0, 0, a))


def crate(name, m, center, size, lid=True):
    rig.box(name, center, size, m["crate"], mask=False)
    x, y, z = center
    if lid:
        rig.box(f"{name}_lid", (x, y, z + size[2] / 2 + 0.01), (size[0] + 0.02, size[1] + 0.02, 0.02), m["crate"])
    for sx in (-1, 1):
        rig.box(f"{name}_handle{sx}", (x + sx * (size[0] / 2 + 0.01), y, z + size[2] * 0.2), (0.02, size[1] * 0.4, 0.02), m["steel"], bevel=0)
    rig.box(f"{name}_band", (x, y, z), (size[0] + 0.01, size[1] + 0.01, 0.025), m["dark"], bevel=0)


# ---------------------------------------------------------------- variants

def machine_gun(m):
    v = VARIANTS["mg"]
    skirts(m)
    hull(m)
    deck_railing(m, DECK)
    for i, y in enumerate(v["mounts"]):
        barbette(f"barbette{i}", m, y, v["radius"], DECK, v["top"])
    # ammunition boxes between the guns, a spare barrel rack and an aerial
    for y in (-0.95, 0.95):
        for sx in (-1, 1):
            crate(f"ammo{y}{sx}", m, (sx * 0.55, y, DECK + 0.1), (0.3, 0.22, 0.18))
        rig.box(f"belt_feed{y}", (0, y, DECK + 0.05), (0.4, 0.12, 0.06), m["brass"], bevel=0.005)
    for k in range(3):
        rig.cylinder(f"spare_barrel{k}", (-0.72 + k * 0.06, -2.5, DECK + 0.1), (-0.72 + k * 0.06, -2.15, DECK + 0.1), 0.022, m["dark"])
    rig.cylinder("aerial", (0.75, 2.45, DECK), (0.75, 2.45, DECK + 0.9), 0.012, m["steel"], verts=6)
    rig.cylinder("aerial_base", (0.75, 2.45, DECK), (0.75, 2.45, DECK + 0.08), 0.045, m["dark"])


def flamethrower(m):
    v = VARIANTS["flame"]
    tank_z, tank_r = 1.48, 0.66
    # cradle on the underframe and armour skirts below the tank
    skirts(m)
    rig.box("cradle", (0, 0, 1.0), (1.6, 2 * HALF_LEN, 0.3), m["armour"], mask=True)
    for k, y in enumerate((-2.3, -0.75, 0.75, 2.3)):
        rig.box(f"saddle{k}", (0, y, 1.1), (1.7, 0.16, 0.3), m["dark"])
    # the tank: cylinder with domed ends, three armour bands and a manway
    rig.cylinder("tank", (0, -HALF_LEN + 0.2, tank_z), (0, HALF_LEN - 0.2, tank_z), tank_r, m["tank"], verts=48, mask=True)
    for sy in (-1, 1):
        cap = rig.cylinder(f"tank_cap{sy}", (0, sy * (HALF_LEN - 0.2), tank_z), (0, sy * (HALF_LEN - 0.02), tank_z),
                           tank_r * 0.92, m["tank"], verts=48, mask=True)
        rig.torus(f"tank_seam{sy}", (0, sy * (HALF_LEN - 0.2), tank_z), tank_r + 0.005, 0.02, m["steel"], rotation=(math.pi / 2, 0, 0))
    for k, y in enumerate((-2.3, -0.75, 0.75, 2.3)):
        rig.torus(f"band{k}", (0, y, tank_z), tank_r + 0.02, 0.035, m["armour"], rotation=(math.pi / 2, 0, 0))
    rig.cylinder("manway", (0, 0, tank_z + tank_r - 0.05), (0, 0, tank_z + tank_r + 0.12), 0.2, m["steel"], verts=24)
    rig.cylinder("manway_lid", (0, 0, tank_z + tank_r + 0.12), (0, 0, tank_z + tank_r + 0.15), 0.23, m["dark"], verts=24)
    rivet_ring("manway_rivets", (0, 0, tank_z + tank_r + 0.15), 0.2, 12, m)
    # walkway along the top with railings
    walk = tank_z + tank_r + 0.02
    for sx in (-1, 1):
        rig.box(f"walkway{sx}", (sx * 0.42, 0, walk), (0.3, 2 * HALF_LEN - 0.6, 0.03), m["deck"])
        for i in range(8):
            y = -HALF_LEN + 0.4 + i * (2 * HALF_LEN - 0.8) / 7
            rig.cylinder(f"walk_post{sx}{i}", (sx * 0.58, y, walk), (sx * 0.58, y, walk + 0.32), 0.013, m["rail"], verts=8)
            rig.box(f"walk_bracket{sx}{i}", (sx * 0.5, y, walk - 0.05), (0.22, 0.04, 0.06), m["dark"], bevel=0)
        rig.cylinder(f"walk_rail{sx}", (sx * 0.58, -HALF_LEN + 0.4, walk + 0.32), (sx * 0.58, HALF_LEN - 0.4, walk + 0.32), 0.016, m["rail"])
    # raised pedestals with barbettes, fed by armoured pipes from the tank
    for i, y in enumerate(v["mounts"]):
        rig.cylinder(f"pedestal{i}", (0, y, walk - 0.05), (0, y, v["top"] - 0.18), v["radius"] * 0.75, m["armour"], verts=32, mask=True)
        barbette(f"barbette{i}", m, y, v["radius"], v["top"] - 0.18, v["top"])
        for sx in (-1, 1):
            rig.tube_path(f"feed{i}{sx}", [
                (sx * 0.55, y - 0.45, tank_z + 0.2), (sx * 0.6, y - 0.45, walk + 0.1), (sx * 0.38, y - 0.2, v["top"] - 0.3),
            ], 0.035, m["steel"])
            rig.torus(f"valve{i}{sx}", (sx * 0.62, y - 0.45, walk - 0.05), 0.06, 0.012, m["hazard"], rotation=(0, math.pi / 2, 0))
    # pressure gauge, filler valves and hazard stripes on the ends
    rig.cylinder("gauge", (0.3, 0.6, walk), (0.3, 0.6, walk + 0.12), 0.06, m["brass"], verts=16)
    for sy in (-1, 1):
        rig.cylinder(f"filler{sy}", (0.0, sy * (HALF_LEN - 0.4), walk), (0.0, sy * (HALF_LEN - 0.4), walk + 0.1), 0.08, m["dark"])
        rig.torus(f"filler_wheel{sy}", (0.0, sy * (HALF_LEN - 0.4), walk + 0.12), 0.08, 0.012, m["hazard"])
    return walk


def rockets(m):
    v = VARIANTS["rocket"]
    skirts(m)
    hull(m)
    deck_railing(m, DECK)
    for i, y in enumerate(v["mounts"]):
        barbette(f"barbette{i}", m, y, v["radius"], DECK, v["top"])
    # rocket crates in the middle and spare rockets in an open rack
    for k, (x, z) in enumerate(((-0.42, 0), (0.42, 0), (0, 0.2))):
        crate(f"rocket_crate{k}", m, (x, 0, DECK + 0.1 + z), (0.36, 0.5, 0.18))
    for k in range(4):
        x = -0.75 + k * 0.08
        rig.cylinder(f"spare_rocket{k}", (x, 2.35, DECK + 0.07), (x, 2.62, DECK + 0.07), 0.03, m["rocket"], verts=10)
        rig.cylinder(f"spare_rocket_tip{k}", (x, 2.62, DECK + 0.07), (x, 2.67, DECK + 0.07), 0.018, m["steel"], verts=10)
    rig.box("rack", (-0.63, 2.5, DECK + 0.03), (0.4, 0.4, 0.04), m["wood"])
    # small loading crane between the launchers
    rig.cylinder("crane_post", (0.75, 2.45, DECK), (0.75, 2.45, DECK + 0.6), 0.04, m["hazard"])
    rig.cylinder("crane_jib", (0.75, 2.45, DECK + 0.58), (0.4, 2.2, DECK + 0.62), 0.03, m["hazard"])
    rig.cylinder("crane_hook", (0.4, 2.2, DECK + 0.62), (0.4, 2.2, DECK + 0.4), 0.008, m["dark"], verts=6)


def build(variant):
    rig.reset()
    m = materials()
    underframe(m)
    if variant == "mg":
        machine_gun(m)
        ends(m, DECK)
        rig.camera(8, 8.5, shift_y=1.2)
    elif variant == "flame":
        walk = flamethrower(m)
        ends(m, walk)
        rig.camera(8, 9, shift_y=1.5)
    else:
        rockets(m)
        ends(m, DECK)
        rig.camera(8, 8.5, shift_y=1.2)
    rig.sun()
    rig.fill_light()


if __name__ == "__main__":
    a = rig.args()
    variant, out = a[0], a[1]
    frames = [int(x) for x in a[2:]] or list(range(128))
    build(variant)
    rig.render_frames(out, frames, lambda i: i / 256, passes=("color", "mask", "shadow"), samples=24)
