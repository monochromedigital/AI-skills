#!/usr/bin/env python3
"""
frame.py - wraps a raw section screenshot in the tablet/phone device frame
used on the Crackwits assessment slides.

Markers are NOT burned in here. Both renderers (PPTX and the Figma plugin)
draw markers as real vector shapes on top, so they stay editable.

Usage:
  python3 frame.py --in shot.png --out framed.png --device tablet
  python3 frame.py --in-dir audit/screens --out-dir audit/framed --device tablet
"""

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

BRAND = json.loads((Path(__file__).parent.parent / "assets" / "brand.json").read_text())

DEVICES = {
    # bezel thickness and corner radius as a fraction of the framed image width
    "tablet": {"bezel": 0.011, "outer_r": 0.030, "inner_r": 0.016, "color": "#1C1B1C", "edge": "#4A484A"},
    "phone":  {"bezel": 0.028, "outer_r": 0.115, "inner_r": 0.085, "color": "#1C1B1C", "edge": "#4A484A"},
    "laptop": {"bezel": 0.008, "outer_r": 0.014, "inner_r": 0.008, "color": "#1C1B1C", "edge": "#4A484A"},
    "plain":  {"bezel": 0.000, "outer_r": 0.012, "inner_r": 0.012, "color": "#00000000", "edge": None},
}

SHADOW_BLUR = 0.012      # fraction of width
SHADOW_OFFSET = 0.004
SHADOW_ALPHA = 110


def rounded_mask(size, radius, supersample=4):
    """Anti-aliased rounded-rectangle mask."""
    w, h = size
    big = Image.new("L", (w * supersample, h * supersample), 0)
    d = ImageDraw.Draw(big)
    d.rounded_rectangle([0, 0, w * supersample - 1, h * supersample - 1],
                        radius=max(1, radius * supersample), fill=255)
    return big.resize((w, h), Image.LANCZOS)


def frame_image(src_path, dest_path, device="tablet", max_h_ratio=None, shadow=True):
    shot = Image.open(src_path).convert("RGBA")
    sw, sh = shot.size

    # Very tall section screenshots get cropped from the top so the slide
    # stays readable; the finding text carries the rest.
    if max_h_ratio and sh > sw * max_h_ratio:
        shot = shot.crop((0, 0, sw, int(sw * max_h_ratio)))
        sw, sh = shot.size

    spec = DEVICES[device]
    bezel = int(round(sw * spec["bezel"] / max(1e-6, 1 - 2 * spec["bezel"]))) if spec["bezel"] else 0
    fw, fh = sw + bezel * 2, sh + bezel * 2

    outer_r = int(fw * spec["outer_r"])
    inner_r = int(fw * spec["inner_r"])

    # screen with rounded corners
    screen = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
    screen.paste(shot, (0, 0), rounded_mask((sw, sh), inner_r))

    if bezel == 0:
        body = screen
    else:
        body = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
        shell = Image.new("RGBA", (fw, fh), spec["color"])
        body.paste(shell, (0, 0), rounded_mask((fw, fh), outer_r))
        if spec["edge"]:
            d = ImageDraw.Draw(body)
            d.rounded_rectangle([1, 1, fw - 2, fh - 2], radius=outer_r,
                                outline=spec["edge"], width=max(2, int(fw * 0.0016)))
        body.alpha_composite(screen, (bezel, bezel))

    if not shadow:
        body.save(dest_path)
        return dest_path, body.size

    blur = max(2, int(fw * SHADOW_BLUR))
    off = int(fw * SHADOW_OFFSET)
    pad = blur * 3
    canvas = Image.new("RGBA", (fw + pad * 2, fh + pad * 2), (0, 0, 0, 0))

    sh_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh_layer)
    sd.rounded_rectangle([pad, pad + off, pad + fw, pad + fh + off],
                         radius=outer_r, fill=(0, 0, 0, SHADOW_ALPHA))
    sh_layer = sh_layer.filter(ImageFilter.GaussianBlur(blur))
    canvas.alpha_composite(sh_layer)
    canvas.alpha_composite(body, (pad, pad))
    canvas.save(dest_path)

    # Report where the live screen sits inside the exported PNG, as fractions.
    # Renderers need this to convert element coords -> marker positions.
    meta = {
        "png_size": canvas.size,
        "screen_rect": {
            "x": (pad + bezel) / canvas.size[0],
            "y": (pad + bezel) / canvas.size[1],
            "w": sw / canvas.size[0],
            "h": sh / canvas.size[1],
        },
        "cropped": bool(max_h_ratio and shot.size[1] != Image.open(src_path).size[1]),
    }
    return dest_path, meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src")
    ap.add_argument("--out", dest="dest")
    ap.add_argument("--in-dir")
    ap.add_argument("--out-dir")
    ap.add_argument("--device", default="tablet", choices=list(DEVICES))
    ap.add_argument("--max-h-ratio", type=float, default=1.6,
                    help="crop screenshots taller than width * this")
    ap.add_argument("--no-shadow", action="store_true")
    args = ap.parse_args()

    out = {}
    if args.in_dir:
        ind, outd = Path(args.in_dir), Path(args.out_dir or (Path(args.in_dir).parent / "framed"))
        outd.mkdir(parents=True, exist_ok=True)
        for p in sorted(ind.glob("*.png")):
            dest = outd / p.name
            _, meta = frame_image(p, dest, args.device, args.max_h_ratio, not args.no_shadow)
            out[p.name] = {"path": str(dest), "meta": meta}
    else:
        _, meta = frame_image(args.src, args.dest, args.device, args.max_h_ratio, not args.no_shadow)
        out[Path(args.src).name] = {"path": args.dest, "meta": meta}

    print(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    main()
