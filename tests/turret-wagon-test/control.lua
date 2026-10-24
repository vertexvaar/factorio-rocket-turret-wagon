-- Headless test scene for the turret wagon mods, run via tests/run.py (factorio --benchmark).
-- Works for whichever of the three mods is active. Every check logs
-- "WAGONTEST PASS ..." or "WAGONTEST FAIL ...", the end "WAGONTEST DONE".

local SPECS = {
  ["gun-turret-wagon"] = { mounts = 3, refill = 10, ammo = "firearm-magazine", amount = 50, distance = 12 },
  ["flamethrower-turret-wagon"] = { mounts = 2, refill = 100, fluid = "light-oil", amount = 1000, distance = 12 },
  -- rockets have a minimum range: their targets keep their distance
  ["rocket-turret-wagon"] = { mounts = 2, refill = 10, ammo = "rocket", amount = 50, distance = 22, hold = true },
}
local MOD, SPEC
for name, spec in pairs(SPECS) do
  if script.active_mods[name] then
    MOD, SPEC = name, spec
  end
end
local TURRET = MOD .. "-turret"

local function report(ok, what, detail)
  log(string.format("WAGONTEST %s %s%s", ok and "PASS" or "FAIL", what, detail and (" (" .. detail .. ")") or ""))
end

local function rail_line(surface, vertical, fixed, from, to)
  for c = from, to, 2 do
    surface.create_entity({
      name = "straight-rail",
      position = vertical and { fixed, c } or { c, fixed },
      direction = vertical and defines.direction.north or defines.direction.east,
      force = "player",
    })
  end
end

-- Locomotive plus turret wagon, both facing east (or north).
local function train(surface, vertical, fixed, wagon_at, quality)
  local dir = vertical and defines.direction.north or defines.direction.east
  local loco_at = vertical and wagon_at - 7 or wagon_at + 7
  local loco = surface.create_entity({
    name = "locomotive",
    force = "player",
    direction = dir,
    position = vertical and { fixed, loco_at } or { loco_at, fixed },
  })
  local wagon = surface.create_entity({
    name = MOD,
    force = "player",
    direction = dir,
    raise_built = true,
    quality = quality,
    position = vertical and { fixed, wagon_at } or { wagon_at, fixed },
  })
  loco.train.manual_mode = true
  return wagon, loco
end

local function fill(wagon, amount)
  if SPEC.fluid then
    wagon.insert_fluid({ name = SPEC.fluid, amount = amount or SPEC.amount })
  else
    wagon.insert({ name = SPEC.ammo, count = amount or SPEC.amount })
  end
end

local function turrets(wagon) return remote.call(MOD, "turrets", wagon) or {} end

local function load_of(entity)
  if SPEC.fluid then return entity.get_fluid_contents()[SPEC.fluid] or 0 end
  local inv = entity.get_inventory(
    entity.type == "cargo-wagon" and defines.inventory.cargo_wagon or defines.inventory.turret_ammo
  )
  return inv.get_item_count(SPEC.ammo)
end

local function mount(wagon, offset)
  local a = wagon.orientation * 2 * math.pi
  return wagon.position.x + math.sin(a) * offset, wagon.position.y - math.cos(a) * offset
end

local function mounts()
  if SPEC.mounts == 2 then return { -1.5, 1.5 } end
  return { -1.9, 0, 1.9 }
end

-- How far the turrets are from their mounts; positions defaults to where they are now.
local function deviation(wagon, positions)
  local worst = 0
  for i, t in pairs(turrets(wagon)) do
    local x, y = mount(wagon, mounts()[i])
    local p = positions and positions[i] or t.position
    worst = math.max(worst, math.abs(p.x - x), math.abs(p.y - y))
  end
  return worst
end

local function positions(wagon)
  local list = {}
  for i, t in pairs(turrets(wagon)) do
    list[i] = t.position
  end
  return list
end

local function alive(list)
  local n = 0
  for _, e in pairs(list) do
    if e.valid then n = n + 1 end
  end
  return n
end

local function setup()
  local surface = game.surfaces.nauvis
  game.map_settings.enemy_expansion.enabled = false
  surface.request_to_generate_chunks({ 0, 0 }, 6)
  surface.force_generate_chunk_requests()
  for _, e in pairs(surface.find_entities_filtered({ force = "enemy" })) do
    e.destroy()
  end
  for _, e in pairs(surface.find_entities_filtered({ area = { { -160, -160 }, { 160, 160 } } })) do
    if e.type ~= "character" then e.destroy() end
  end
  local tiles = {}
  for x = -160, 159 do
    for y = -160, 159 do
      tiles[#tiles + 1] = { name = "lab-dark-1", position = { x, y } }
    end
  end
  surface.set_tiles(tiles)

  local s = { surface = surface }
  storage.scene = s
  storage.start = game.tick

  -- A: standing train, horizontal
  rail_line(surface, false, 1, -61, 61)
  s.a, s.a_loco = train(surface, false, 1, -9)
  report(s.a and s.a.valid, "wagon can be built on rails")
  report(#turrets(s.a) == SPEC.mounts, "wagon gets its turrets", #turrets(s.a) .. " turrets")
  local all_safe = true
  for _, t in pairs(turrets(s.a)) do
    all_safe = all_safe and t.valid and not t.destructible and t.name == TURRET and t.force.name == "player"
  end
  report(all_safe, "turrets are indestructible and belong to the wagon's force")
  report(deviation(s.a) < 0.01, "turrets sit on the wagon axis", string.format("%.3f", deviation(s.a)))
  fill(s.a)

  -- B: moving train with enemies along the track
  rail_line(surface, false, -81, -151, 151)
  s.b, s.b_loco = train(surface, false, -81, -130)
  fill(s.b)
  s.b_start = s.b.position.x

  -- C: vertical train
  rail_line(surface, true, 101, -61, 61)
  s.c = train(surface, true, 101, 0)
  local cx = turrets(s.c)[1]
  report(
    cx and math.abs(cx.position.x - s.c.position.x) < 0.01 and math.abs(cx.position.y - s.c.position.y) > 1,
    "turrets follow a vertical wagon",
    string.format("%.3f", deviation(s.c))
  )

  -- D/E: removal paths
  rail_line(surface, false, 61, -61, 61)
  s.d = train(surface, false, 61, -30)
  s.e = train(surface, false, 61, 20)
  s.d_turrets = turrets(s.d)
  s.e_turrets = turrets(s.e)

  -- F: quality wagon gets quality turrets
  if script.active_mods["quality"] then
    rail_line(surface, false, 121, -61, 61)
    s.f = train(surface, false, 121, 0, "rare")
    local t = turrets(s.f)[1]
    report(t and t.quality.name == "rare", "turrets share the wagon's quality", t and t.quality.name)
  end

  -- G: elevated rails
  if prototypes.entity["elevated-straight-rail"] then
    for x = -61, 61, 2 do
      surface.create_entity({
        name = "elevated-straight-rail",
        position = { x, 141 },
        direction = defines.direction.east,
        force = "player",
      })
    end
    s.g = train(surface, false, 141, 0)
    local t = turrets(s.g)[1]
    report(t and t.name == TURRET .. "-elevated", "wagon on a bridge gets elevated turrets", t and t.name)
    local draw = s.g.draw_data.position
    report(
      t and math.abs(t.position.y - draw.y) < 0.01,
      "elevated turrets sit on the drawn wagon",
      t and string.format("turret y %.2f, wagon drawn at %.2f", t.position.y, draw.y)
    )
    fill(s.g)
  end

  -- an empty wagon must not do anything bad
  rail_line(surface, true, -101, -41, 41)
  s.empty = train(surface, true, -101, 0)
end

local function check_loaded()
  local s = storage.scene
  local total, each_full = load_of(s.a), true
  for _, t in pairs(turrets(s.a)) do
    total = total + load_of(t)
    each_full = each_full and load_of(t) >= SPEC.refill - 1
  end
  report(each_full, "turrets are loaded from the wagon")
  report(math.abs(total - SPEC.amount) < 1, "no ammo created or lost", string.format("%.1f of %d", total, SPEC.amount))
  for _, t in pairs(turrets(s.empty)) do
    if load_of(t) ~= 0 then report(false, "empty wagon leaves turrets empty") end
  end
end

local function spawn_enemies()
  local s = storage.scene
  s.a_enemies = {}
  for i = -2, 2 do
    local biter =
      s.surface.create_entity({ name = "small-biter", force = "enemy", position = { -9 + i * 2, 1 + SPEC.distance } })
    if SPEC.hold then
      biter.commandable.set_command({ type = defines.command.stop, ticks_to_wait = 100000 })
    else
      biter.commandable.set_command({ type = defines.command.attack, target = s.a })
    end
    s.a_enemies[#s.a_enemies + 1] = biter
  end
  report(alive(s.a_enemies) == 5, "enemies spawned near the standing train")
end

local function spawn_track_enemies()
  local s = storage.scene
  s.b_enemies = {}
  for x = -60, 60, 30 do
    local biter =
      s.surface.create_entity({ name = "small-biter", force = "enemy", position = { x, -81 - SPEC.distance } })
    -- stay put, so the train has to hit them while passing
    biter.commandable.set_command({ type = defines.command.stop, ticks_to_wait = 100000 })
    s.b_enemies[#s.b_enemies + 1] = biter
  end
  s.b_loco.train.speed = 0.35
end

script.on_event(defines.events.on_tick, function()
  if not MOD then
    report(false, "no turret wagon mod active")
    log("WAGONTEST DONE")
    return
  end
  if not storage.scene then
    setup()
    return
  end
  local s = storage.scene
  local age = game.tick - storage.start
  if age == 2 then spawn_track_enemies() end
  if age > 2 and age < 1200 and s.b.valid then
    -- turrets are placed for the wagon position after this tick's train update,
    -- so compare last tick's turret positions with the wagon now
    if s.b_last and age > 5 then s.b_worst = math.max(s.b_worst or 0, deviation(s.b, s.b_last)) end
    s.b_last = positions(s.b)
    -- the train keeps going; give it a little push against friction
    if s.b_loco.train.speed < 0.3 and s.b.position.x < 90 then s.b_loco.train.speed = 0.3 end
  end
  if age == 10 then
    s.d.die()
    s.e.destroy({ raise_destroy = true })
    local gone = true
    for _, t in pairs(s.e_turrets) do
      gone = gone and not t.valid
    end
    report(gone, "script-destroyed wagon removes its turrets")
  end
  if age == 12 then
    local gone = true
    for _, t in pairs(s.d_turrets) do
      gone = gone and not t.valid
    end
    report(gone, "destroyed wagon removes its turrets")
  end
  if age == 70 then
    check_loaded()
    if s.g then
      local loaded = true
      for _, t in pairs(turrets(s.g)) do
        loaded = loaded and load_of(t) > 0
      end
      report(loaded, "elevated turrets are loaded too")
    end
  end
  if age == 80 then spawn_enemies() end
  if age == 1200 then
    report(
      s.b.position.x - s.b_start > 200,
      "test train moved",
      string.format("%.1f tiles", s.b.position.x - s.b_start)
    )
    report((s.b_worst or 1) < 0.05, "turrets stay on the moving wagon", string.format("max %.4f", s.b_worst or -1))
  end
  if age == 1300 then
    report(alive(s.a_enemies) == 0, "standing train kills nearby enemies", alive(s.a_enemies) .. " left")
    report(
      s.a.health > s.a.max_health * 0.9,
      "wagon survives the fight",
      string.format(
        "wagon %.0f/%.0f, locomotive %.0f/%.0f",
        s.a.health,
        s.a.max_health,
        s.a_loco.health,
        s.a_loco.max_health
      )
    )
    for _, e in pairs(s.b_enemies) do
      if e.valid then log(string.format("WAGONDEBUG left %.1f,%.1f hp %.0f", e.position.x, e.position.y, e.health)) end
    end
    report(alive(s.b_enemies) == 0, "moving train kills enemies along the track", alive(s.b_enemies) .. " left")
    local expected = 0
    for _, wagon in pairs(s.surface.find_entities_filtered({ name = MOD })) do
      expected = expected + SPEC.mounts
    end
    local count = s.surface.count_entities_filtered({ name = { TURRET, TURRET .. "-elevated" } })
    report(count == expected, "no orphaned turrets", count .. " turrets, " .. expected .. " expected")
    log("WAGONTEST DONE")
  end
end)
