"""Post-processing for Blender renders (run with normal Python, needs Pillow + numpy).

  python tools/blender/pack.py frame <render_dir> <kind> <index>      -> PIL image (library use)
  python tools/blender/pack.py preview <render_dir> <out.png> <tint hex> <frames...>
  python tools/blender/pack.py sheet <render_dir> <out_prefix> <count> <line_length> <lines_per_file>

Frames are rendered at 2x and downsampled here to the final 64 px per tile (used at scale 0.5).
"""
import math
import os
import sys

import numpy as np
from PIL import Image

SUPERSAMPLE = 2
MASK_STRENGTH = 0.75  # vanilla masks do not tint at full strength either
MASK_GREY = 160


# Buildings sit on the square tile grid, so their renders are stretched vertically
# until the ground footprint is square again (rolling stock is not, like vanilla).
GROUND_STRETCH = 1 / math.sin(math.radians(50))


def load(render_dir, kind, index, stretch=1.0):
    im = Image.open(os.path.join(render_dir, f"{kind}_{index:03d}.png")).convert("RGBA")
    w = im.width // SUPERSAMPLE
    h = round(im.height * stretch / SUPERSAMPLE)
    im = im.resize((w, h), Image.LANCZOS)
    if kind == "shadow":
        a = np.asarray(im).astype(np.float32)
        alpha = a[..., 3]
        out = np.zeros_like(a)
        out[..., 3] = alpha
        im = Image.fromarray(out.astype(np.uint8))
    elif kind == "mask":
        a = np.asarray(im).astype(np.float32)
        out = np.zeros_like(a)
        # Factorio overlays (mask colour x tint) onto the sprite: below 0.5 that is
        # 2 * mask * tint * sprite. Grey 160 keeps the paint about as bright as rendered.
        out[..., 0:3] = MASK_GREY
        out[..., 3] = a[..., 3] * (a[..., 0] / 255.0) * MASK_STRENGTH
        im = Image.fromarray(out.astype(np.uint8))
    return im


def tinted(color, mask, tint):
    """Approximates Factorio's tint_as_overlay for a preview."""
    c = np.asarray(color).astype(np.float32) / 255
    m = np.asarray(mask).astype(np.float32)[..., 3:4] / 255
    t = np.array(tint, dtype=np.float32).reshape(1, 1, 3)
    base = c[..., :3]
    a = MASK_GREY / 255 * t
    over = np.where(a < 0.5, 2 * a * base, 1 - 2 * (1 - a) * (1 - base))
    rgb = base * (1 - m) + over * m
    out = np.concatenate([rgb, c[..., 3:4]], axis=2)
    return Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8))


def ground(w, h):
    rng = np.random.default_rng(1)
    g = np.full((h, w, 3), (88, 72, 50), dtype=np.float32)
    g += rng.normal(0, 6, (h, w, 1))
    return Image.fromarray(np.clip(g, 0, 255).astype(np.uint8)).convert("RGBA")


def composite(render_dir, index, tint):
    color = load(render_dir, "color", index)
    mask = load(render_dir, "mask", index)
    shadow = load(render_dir, "shadow", index)
    bg = ground(color.width, color.height)
    sh = np.asarray(shadow).astype(np.float32)
    sh[..., 3] *= 0.6
    bg.alpha_composite(Image.fromarray(sh.astype(np.uint8)))
    bg.alpha_composite(tinted(color, mask, tint))
    return bg


def hex_rgb(h):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]


def preview(render_dir, out, tint, frames):
    tiles = [composite(render_dir, i, hex_rgb(tint)) for i in frames]
    w = sum(t.width for t in tiles)
    h = max(t.height for t in tiles)
    sheet = Image.new("RGBA", (w, h))
    x = 0
    for t in tiles:
        sheet.paste(t, (x, 0))
        x += t.width
    sheet.save(out)


def bbox_union(render_dir, kinds, count):
    box = None
    for kind in kinds:
        for i in range(count):
            b = load(render_dir, kind, i).getbbox()
            if b:
                box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
    return box


def sheet(render_dir, prefix, count, line_length, lines_per_file, kinds=("color", "mask", "shadow")):
    """Writes <prefix>-<kind>-<n>.png sheets and returns lua-ready metadata per kind."""
    meta = {}
    for kind in kinds:
        first = load(render_dir, kind, 0)
        full_w, full_h = first.size
        box = bbox_union(render_dir, [kind], count)
        # keep the crop symmetric horizontally/vertically around the origin is not required:
        # Factorio takes the offset as shift.
        w, h = box[2] - box[0], box[3] - box[1]
        per_file = line_length * lines_per_file
        files = []
        for f in range(math.ceil(count / per_file)):
            n = min(per_file, count - f * per_file)
            lines = math.ceil(n / line_length)
            img = Image.new("RGBA", (w * line_length, h * lines))
            for k in range(n):
                frame = load(render_dir, kind, f * per_file + k).crop(box)
                img.paste(frame, ((k % line_length) * w, (k // line_length) * h))
            name = f"{prefix}-{kind}-{f + 1}.png"
            img.save(name, optimize=True)
            files.append(os.path.basename(name))
        cx = (box[0] + box[2]) / 2 - full_w / 2
        cy = (box[1] + box[3]) / 2 - full_h / 2
        meta[kind] = {"width": w, "height": h, "files": files, "shift": (cx / 64, cy / 64)}
    return meta


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "preview":
        preview(sys.argv[2], sys.argv[3], sys.argv[4], [int(x) for x in sys.argv[5:]])
    elif cmd == "sheet":
        import json
        print(json.dumps(sheet(sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6]))))


def rails_vertical(img, x_center_px, color=(150, 150, 145, 255)):
    """Draws a simple north-south track (ties and two rails) for previews."""
    from PIL import ImageDraw
    d = ImageDraw.Draw(img)
    for y in range(0, img.height, 22):
        d.rectangle((x_center_px - 52, y, x_center_px + 52, y + 9), fill=(70, 55, 40, 255))
    for dx in (-34, 34):
        d.rectangle((x_center_px + dx - 4, 0, x_center_px + dx + 4, img.height), fill=color)


def scene(size_tiles, layers, rails_x=None):
    """layers: list of (PIL image rendered around the world origin, (dx, dy) tiles, shadow?)."""
    w, h = round(size_tiles[0] * 64), round(size_tiles[1] * 64)
    img = ground(w, h)
    if rails_x is not None:
        rails_vertical(img, w // 2 + round(rails_x * 64))
    for im, (dx, dy), is_shadow in layers:
        if is_shadow:
            a = np.asarray(im).astype(np.float32)
            a[..., 3] *= 0.6
            im = Image.fromarray(a.astype(np.uint8))
        x = w // 2 + round(dx * 64) - im.width // 2
        y = h // 2 + round(dy * 64) - im.height // 2
        img.alpha_composite(im, (x, y)) if x >= 0 and y >= 0 else img.paste(im, (x, y), im)
    return img
