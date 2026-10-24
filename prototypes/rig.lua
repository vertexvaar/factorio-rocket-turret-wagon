-- Helpers that turn a vanilla turret into the hidden roof turret of a wagon.
local rig = {}

-- Adds dy to the shift of every sprite in an animation tree, so the turret
-- head sits on the wagon roof instead of on the ground.
function rig.lift(node, dy)
  if type(node) ~= "table" then return end
  if node.filename or node.filenames or node.stripes then
    local shift = node.shift or { 0, 0 }
    node.shift = { shift[1] or shift.x or 0, (shift[2] or shift.y or 0) + dy }
    return
  end
  for _, child in pairs(node) do
    rig.lift(child, dy)
  end
end

local ANIMATIONS = {
  "folded_animation",
  "preparing_animation",
  "prepared_animation",
  "prepared_alternative_animation",
  "starting_attack_animation",
  "attacking_animation",
  "ending_attack_animation",
  "folding_animation",
  "energy_glow_animation",
  "muzzle_animation",
}

-- Copies a turret prototype and strips everything that would make it a building:
-- no base, no collision, not selectable, not minable, not shown anywhere.
function rig.turret(source, name, lift)
  local turret = table.deepcopy(source)
  turret.name = name
  turret.localised_name = { "entity-name." .. name }
  turret.flags = {
    "placeable-off-grid",
    "not-on-map",
    "not-blueprintable",
    "not-deconstructable",
    "not-upgradable",
    "not-flammable",
    "not-in-kill-statistics",
    "no-automated-item-insertion",
    "no-automated-item-removal",
  }
  turret.hidden = true
  turret.hidden_in_factoriopedia = true
  turret.minable = nil
  turret.placeable_by = nil
  turret.fast_replaceable_group = nil
  turret.next_upgrade = nil
  turret.corpse = nil
  turret.dying_explosion = nil
  turret.collision_box = { { -0.4, -0.4 }, { 0.4, 0.4 } }
  turret.collision_mask = { layers = {} }
  turret.selection_box = { { -0.4, -0.4 }, { 0.4, 0.4 } }
  turret.selectable_in_game = false
  turret.is_military_target = false
  turret.circuit_connector = nil
  turret.circuit_wire_max_distance = nil
  turret.water_reflection = nil
  turret.graphics_set = {}
  turret.gun_animation_render_layer = "higher-object-under"
  turret.factoriopedia_simulation = nil
  -- a turret on a moving train has little time per target: turn and unfold faster
  turret.rotation_speed = (turret.rotation_speed or 0.02) * 3
  turret.preparing_speed = (turret.preparing_speed or 0.08) * 2
  turret.folding_speed = (turret.folding_speed or 0.08) * 2
  for _, key in pairs(ANIMATIONS) do
    rig.lift(turret[key], lift)
  end
  -- shots must leave the lifted barrel, not the ground below it
  local attack = turret.attack_parameters
  if attack.projectile_center then
    local c = attack.projectile_center
    attack.projectile_center = { c[1] or c.x or 0, (c[2] or c.y or 0) + lift }
  end
  if attack.gun_center_shift then
    local shift = attack.gun_center_shift
    if shift.north then
      for direction, v in pairs(shift) do
        shift[direction] = { v[1] or v.x or 0, (v[2] or v.y or 0) + lift }
      end
    else
      attack.gun_center_shift = { shift[1] or shift.x or 0, (shift[2] or shift.y or 0) + lift }
    end
  end
  return turret
end

-- The same turret, drawn above elevated rails. The script swaps a wagon's
-- turrets to this variant while the wagon is up on a bridge.
function rig.elevated(turret)
  local high = table.deepcopy(turret)
  high.name = turret.name .. "-elevated"
  high.gun_animation_render_layer = "elevated-higher-object"
  return high
end

-- Standard rolling stock armour for the turret wagons.
function rig.armour(wagon)
  wagon.max_health = 1000
  wagon.resistances = {
    { type = "physical", decrease = 5, percent = 30 },
    { type = "explosion", decrease = 10, percent = 30 },
    { type = "acid", decrease = 3, percent = 20 },
    { type = "fire", decrease = 5, percent = 50 },
    { type = "impact", decrease = 50, percent = 60 },
  }
end

return rig
