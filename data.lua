local config = require("config")
local rig = require("prototypes.rig")
local graphics = require("prototypes.graphics")

-- With Space Age the roof launchers are rocket turrets. Without it, the rocket
-- launcher's stats on a gun turret body.
local space_age = data.raw["ammo-turret"]["rocket-turret"] ~= nil

-- The wagon: a cargo wagon whose cargo feeds the rocket launchers on its roof.
local wagon = table.deepcopy(data.raw["cargo-wagon"]["cargo-wagon"])
wagon.name = config.wagon
wagon.icons = {
  { icon = "__base__/graphics/icons/cargo-wagon.png", icon_size = 64 },
  space_age
      and { icon = "__space-age__/graphics/icons/rocket-turret.png", icon_size = 64, scale = 0.3, shift = { 8, -8 } }
    or { icon = "__base__/graphics/icons/rocket-launcher.png", icon_size = 64, scale = 0.3, shift = { 8, -8 } },
}
wagon.icon = nil
wagon.minable = { mining_time = 0.5, result = config.wagon }
wagon.inventory_size = 10
wagon.color = { r = 0.3, g = 0.33, b = 0.38, a = 1 }
wagon.allow_manual_color = true
wagon.factoriopedia_simulation = nil
rig.armour(wagon)
local pictures = graphics.wagon_pictures()
if pictures then
  wagon.pictures = pictures
  -- an armoured wagon has no sliding doors
  wagon.horizontal_doors = nil
  wagon.vertical_doors = nil
end
wagon.icons = graphics.icons(
  space_age and "__space-age__/graphics/icons/rocket-turret.png" or "__base__/graphics/icons/rocket-launcher.png"
) or wagon.icons

local item = table.deepcopy(data.raw["item-with-entity-data"]["cargo-wagon"])
item.name = config.wagon
item.icons = wagon.icons
item.icon = nil
item.place_result = config.wagon
item.order = "c[rolling-stock]-b[cargo-wagon]-u[rocket-turret-wagon]"

local turret
if space_age then
  turret = rig.turret(data.raw["ammo-turret"]["rocket-turret"], config.turret, -0.9)
  -- it rides in the open and needs no heating on Aquilo
  turret.heating_energy = nil
else
  turret = rig.turret(data.raw["ammo-turret"]["gun-turret"], config.turret, -0.75)
  turret.attack_parameters = {
    type = "projectile",
    ammo_category = "rocket",
    cooldown = 60,
    projectile_creation_distance = 0.6,
    projectile_center = { 0, -0.75 },
    range = 36,
    sound = data.raw["gun"]["rocket-launcher"].attack_parameters.sound,
  }
end
-- explosions must stay clear of the train, but enemies at the train should still be hit
turret.attack_parameters.min_range = 8

data:extend({
  wagon,
  item,
  {
    type = "recipe",
    name = config.wagon,
    energy_required = 5,
    enabled = false,
    ingredients = space_age and {
      { type = "item", name = "cargo-wagon", amount = 1 },
      { type = "item", name = "rocket-turret", amount = 2 },
      { type = "item", name = "steel-plate", amount = 20 },
    } or {
      { type = "item", name = "cargo-wagon", amount = 1 },
      { type = "item", name = "rocket-launcher", amount = 2 },
      { type = "item", name = "steel-plate", amount = 20 },
      { type = "item", name = "advanced-circuit", amount = 10 },
    },
    results = { { type = "item", name = config.wagon, amount = 1 } },
  },
  {
    type = "technology",
    name = config.wagon,
    icons = {
      { icon = "__base__/graphics/technology/railway.png", icon_size = 256 },
      space_age
          and {
            icon = "__space-age__/graphics/technology/rocket-turret.png",
            icon_size = 256,
            scale = 0.25,
            shift = { 32, 32 },
          }
        or { icon = "__base__/graphics/technology/rocketry.png", icon_size = 256, scale = 0.25, shift = { 32, 32 } },
    },
    effects = { { type = "unlock-recipe", recipe = config.wagon } },
    prerequisites = { "railway", space_age and "rocket-turret" or "rocketry" },
    unit = space_age and {
      count = 500,
      ingredients = {
        { "automation-science-pack", 1 },
        { "logistic-science-pack", 1 },
        { "military-science-pack", 1 },
        { "chemical-science-pack", 1 },
        { "space-science-pack", 1 },
        { "agricultural-science-pack", 1 },
      },
      time = 30,
    } or {
      count = 200,
      ingredients = {
        { "automation-science-pack", 1 },
        { "logistic-science-pack", 1 },
        { "military-science-pack", 1 },
        { "chemical-science-pack", 1 },
      },
      time = 30,
    },
  },
})
data:extend(rig.variants(turret, config.mounts))
