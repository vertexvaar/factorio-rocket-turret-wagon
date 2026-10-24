-- In-game tests with a real player (tests/ingame.py runs it in a game window).
-- Writes WAGONTEST lines to script-output/wagon-ingame/report.txt.

local SPECS = {
  ["gun-turret-wagon"] = { ammo = "firearm-magazine", mounts = 3 },
  ["flamethrower-turret-wagon"] = { fluid = "light-oil", mounts = 2 },
  ["rocket-turret-wagon"] = { ammo = "rocket", mounts = 2 },
}
local MOD, SPEC
for name, spec in pairs(SPECS) do
  if script.active_mods[name] then
    MOD, SPEC = name, spec
  end
end
local TURRETS = { MOD .. "-turret", MOD .. "-turret-elevated" }

script.on_init(function()
  if remote.interfaces.freeplay then
    remote.call("freeplay", "set_disable_crashsite", true)
    remote.call("freeplay", "set_skip_intro", true)
  end
end)

local function report(ok, what, detail)
  helpers.write_file(
    "wagon-ingame/report.txt",
    string.format("WAGONTEST %s %s%s\n", ok and "PASS" or "FAIL", what, detail and (" (" .. detail .. ")") or ""),
    true
  )
end

local function turrets(wagon) return remote.call(MOD, "turrets", wagon) or {} end

local function rail_line(surface, y, from, to)
  for x = from, to, 2 do
    surface.create_entity({
      name = "straight-rail",
      position = { x, y },
      direction = defines.direction.east,
      force = "player",
    })
  end
end

local function turret_count(surface) return surface.count_entities_filtered({ name = TURRETS }) end

local steps = {}
local s = {}

-- built by the player from the cursor
steps[1] = function(player)
  local surface = player.surface
  rail_line(surface, 11, -21, 21)
  player.teleport({ 0, 7 })
  player.cursor_stack.set_stack({ name = MOD, count = 1 })
  player.build_from_cursor({ position = { 0, 11 }, direction = defines.direction.east })
  s.wagon = surface.find_entities_filtered({ name = MOD })[1]
  report(s.wagon ~= nil, "player can place the wagon")
  report(s.wagon and #turrets(s.wagon) == SPEC.mounts, "placed wagon gets its turrets")
  if SPEC.fluid then
    s.wagon.insert_fluid({ name = SPEC.fluid, amount = 1000 })
  else
    s.wagon.insert({ name = SPEC.ammo, count = 40 })
  end
end

-- after the turrets loaded up, the player mines the wagon
steps[60] = function(player)
  player.clear_cursor()
  player.get_main_inventory().clear()
  player.get_inventory(defines.inventory.character_ammo).clear()
  local ok = player.mine_entity(s.wagon, true)
  report(ok, "player can mine the wagon")
  local inv = player.get_main_inventory()
  report(inv.get_item_count(MOD) == 1, "mined wagon returns to the inventory")
  if not SPEC.fluid then
    -- magazines may go to the character's ammo slots
    local count = player.get_item_count(SPEC.ammo)
    report(count == 40, "mined wagon returns cargo and the turrets' ammo", count .. " of 40")
  end
  report(turret_count(player.surface) == 0, "no turrets left behind", turret_count(player.surface))
end

-- a ghost revived by script (as robots and other mods do)
steps[70] = function(player)
  local ghost = player.surface.create_entity({
    name = "entity-ghost",
    inner_name = MOD,
    position = { 0, 11 },
    direction = defines.direction.east,
    force = "player",
  })
  local _, wagon = ghost.revive({ raise_revive = true })
  report(wagon and #turrets(wagon) == SPEC.mounts, "revived ghost gets its turrets")
  s.revived = wagon
end

-- blueprinting the wagon does not pick up the hidden turrets
steps[80] = function(player)
  local stack = player.cursor_stack
  stack.set_stack({ name = "blueprint" })
  stack.create_blueprint({
    surface = player.surface,
    force = player.force,
    area = { { -5, 8 }, { 5, 14 } },
    include_trains = true,
  })
  local names = {}
  for _, e in pairs(stack.get_blueprint_entities() or {}) do
    names[e.name] = (names[e.name] or 0) + 1
  end
  report(names[MOD] == 1 and not names[TURRETS[1]], "blueprint holds the wagon but no turrets", serpent.line(names))
  player.clear_cursor()
  helpers.write_file("wagon-ingame/report.txt", "WAGONTEST DONE\n", true)
end

local started
script.on_event(defines.events.on_tick, function(event)
  local player = game.get_player(1)
  if not MOD or not player or not player.character then return end
  started = started or event.tick
  local step = steps[event.tick - started + 1]
  if step then
    local ok, err = pcall(step, player)
    if not ok then report(false, "step crashed", tostring(err)) end
  end
end)
