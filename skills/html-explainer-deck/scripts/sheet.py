#!/usr/bin/env python3
"""sheet.py — contact sheet(s) of slide screenshots for one-glance review.
usage: python3 sheet.py shots/ [--prefix d] [--cols 4] [--per 12] [--width 520]
writes shots/sheet-<prefix>-1.png, -2.png … (PIL; falls back to ImageMagick `montage`)."""
import argparse, glob, os, shutil, subprocess, sys
ap = argparse.ArgumentParser(); ap.add_argument('dir'); ap.add_argument('--prefix', default='d')
ap.add_argument('--cols', type=int, default=4); ap.add_argument('--per', type=int, default=12)
ap.add_argument('--width', type=int, default=520)
a = ap.parse_args()
files = sorted(f for f in glob.glob(os.path.join(a.dir, a.prefix + '[0-9]*.png')))
if not files:
    sys.exit(f'no {a.prefix}NN.png in {a.dir}')
chunks = [files[i:i + a.per] for i in range(0, len(files), a.per)]
outs = []
try:
    from PIL import Image, ImageDraw
    for ci, ch in enumerate(chunks):
        ims = [Image.open(f).convert('RGB') for f in ch]
        w = a.width; h = max(int(im.height * w / im.width) for im in ims); pad = 14; lab = 26
        cols = min(a.cols, len(ims)); rows = (len(ims) + cols - 1) // cols
        sheet = Image.new('RGB', (cols * (w + pad) + pad, rows * (h + pad + lab) + pad), (38, 38, 46))
        d = ImageDraw.Draw(sheet)
        for k, (f, im) in enumerate(zip(ch, ims)):
            x = pad + (k % cols) * (w + pad); y = pad + (k // cols) * (h + pad + lab)
            sheet.paste(im.resize((w, int(im.height * w / im.width))), (x, y + lab))
            d.text((x + 2, y + 6), os.path.basename(f), fill=(230, 230, 235))
        o = os.path.join(a.dir, f'sheet-{a.prefix}-{ci+1}.png'); sheet.save(o); outs.append(o)
except ImportError:
    if not shutil.which('montage'):
        sys.exit('need Pillow (pip install pillow) or ImageMagick montage')
    for ci, ch in enumerate(chunks):
        o = os.path.join(a.dir, f'sheet-{a.prefix}-{ci+1}.png')
        subprocess.run(['montage', *ch, '-tile', f'{a.cols}x', '-geometry', f'{a.width}x+8+8', '-background', '#26262e', o], check=True)
        outs.append(o)
print('\n'.join(outs))
