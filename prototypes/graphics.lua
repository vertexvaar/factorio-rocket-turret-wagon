-- Wagon sprites from graphics/entity/sprites.lua, which tools/blender/build_sprites.py
-- generates from the Blender renders. Without that file the wagon keeps the vanilla look.
local config = require("config")

local graphics = {}
local ok, sprites = pcall(require, "graphics.entity.sprites")
sprites = ok and type(sprites) == "table" and sprites or nil

local path = "__" .. config.wagon .. "__/graphics/"

local function sheet(meta, extra)
  local def = {
    width = meta.width,
    height = meta.height,
    shift = meta.shift,
    scale = 0.5,
    direction_count = meta.frame_count,
    back_equals_front = true,
    allow_low_quality_rotation = true,
    usage = "train",
    line_length = meta.line_length,
  }
  if #meta.files == 1 then
    def.filename = path .. "entity/" .. meta.files[1]
  else
    def.filenames = {}
    for i, f in ipairs(meta.files) do
      def.filenames[i] = path .. "entity/" .. f
    end
    def.lines_per_file = meta.lines_per_file
  end
  for k, v in pairs(extra or {}) do
    def[k] = v
  end
  return def
end

-- RollingStockRotatedSlopedGraphics for the wagon, or nil without renders.
function graphics.wagon_pictures()
  if not sprites then return nil end
  local set = sprites.wagon
  return {
    rotated = {
      layers = {
        sheet(set.color),
        sheet(set.mask, { flags = { "mask" }, apply_runtime_tint = true, tint_as_overlay = true }),
        sheet(set.shadow, { draw_as_shadow = true }),
      },
    },
  }
end

-- Item and entity icon, or nil without renders.
function graphics.icons(badge)
  if not sprites then return nil end
  return {
    { icon = path .. "icons/wagon.png", icon_size = 64 },
    { icon = badge, icon_size = 64, scale = 0.3, shift = { 8, -8 } },
  }
end

return graphics
