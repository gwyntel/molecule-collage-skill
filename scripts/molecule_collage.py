#!/usr/bin/env python3
"""Resolve chemical identities and render deterministic, verified molecule art."""
import argparse
import hashlib
import io
import json
import math
import os
from pathlib import Path
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import urlopen

from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageOps
from rdkit import Chem
from rdkit.Chem import rdDepictor
from rdkit.Chem.Draw import rdMolDraw2D


def atomic_bytes(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(dir=path.parent, prefix='.' + path.name)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def write_json(path, obj):
    atomic_bytes(path, (json.dumps(obj, indent=2, ensure_ascii=False) + '\n').encode())


def validate_image(path):
    path = Path(path)
    with Image.open(path) as image:
        image.verify()
    with Image.open(path) as image:
        image.load()  # Required: verify() alone does not decode every row.
        image.getpixel((image.width - 1, image.height - 1))
        result = {'width': image.width, 'height': image.height, 'mode': image.mode}
    result.update(sha256=hashlib.sha256(path.read_bytes()).hexdigest(), full_decode=True)
    return result


def save_image(path, image):
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    atomic_bytes(path, buffer.getvalue())
    return validate_image(path)


def pubchem(url):
    for attempt in range(3):
        try:
            with urlopen(url, timeout=20) as response:
                result = json.load(response)
            time.sleep(.22)
            return result
        except HTTPError as error:
            if error.code not in (429, 500, 502, 503, 504) or attempt == 2:
                raise
        except (URLError, TimeoutError):
            if attempt == 2:
                raise
        time.sleep(1 + attempt)
    raise RuntimeError('PubChem lookup failed')


def resolve(config, online=False):
    records = config.get('compounds')
    if not isinstance(records, list) or not records or len(records) > 100:
        raise ValueError('compounds must contain 1–100 records')
    result = dict(config)
    result['compounds'] = []
    for record in records:
        item = dict(record)
        if not isinstance(item.get('name'), str) or not item['name'].strip():
            raise ValueError('Every compound needs a nonempty name')
        if item.get('group', 'main') not in ('main', 'secondary'):
            raise ValueError('group must be main or secondary')
        if not item.get('smiles'):
            if not online:
                raise ValueError('Unresolved compound: run resolve first: ' + item['name'])
            if item.get('cid'):
                endpoint = 'cid/' + str(int(item['cid']))
            else:
                endpoint = 'name/' + quote(item.get('query', item['name']), safe='')
            url = 'https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/' + endpoint + '/property/IsomericSMILES,MolecularFormula/JSON'
            rows = pubchem(url)['PropertyTable']['Properties']
            if len(rows) != 1:
                raise ValueError('Ambiguous PubChem result; supply a CID: ' + item['name'])
            row = rows[0]
            item.update(cid=row['CID'], smiles=row.get('SMILES') or row.get('IsomericSMILES'),
                        formula=row.get('MolecularFormula'), source='https://pubchem.ncbi.nlm.nih.gov/compound/' + str(row['CID']))
        mol = Chem.MolFromSmiles(item['smiles'])
        if mol is None or mol.GetNumAtoms() == 0:
            raise ValueError('Invalid or empty structure: ' + item['name'])
        item['smiles'] = Chem.MolToSmiles(mol, isomericSmiles=True)
        item['fragments'] = len(Chem.GetMolFrags(mol))
        result['compounds'].append(item)
    return result


def number(config, key, default, low, high, integral=False):
    value = config.get(key, default)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(key + ' must be a finite number')
    if not low <= value <= high or (integral and value != int(value)):
        raise ValueError(key + ' outside supported range')
    return int(value) if integral else value


def boxes_for(config, width, height):
    items = config['compounds']
    if any('box' in item for item in items):
        if not all('box' in item for item in items):
            raise ValueError('Custom layout requires a box for every compound')
        boxes = [item['box'] for item in items]
    else:
        columns = number(config, 'columns', 3, 1, 8, True)
        margin = max(24, int(width * .025))
        main = [i for i, item in enumerate(items) if item.get('group', 'main') == 'main']
        secondary = [i for i, item in enumerate(items) if item.get('group') == 'secondary']
        split = int(height * .80) if main and secondary else height - margin
        boxes = [None] * len(items)
        for indices, top, bottom, cols in [(main, margin, split, columns),
                                           (secondary, split + margin if main else margin, height-margin, 3)]:
            if not indices:
                continue
            rows = math.ceil(len(indices) / cols)
            cell_w = (width - 2 * margin) // cols
            cell_h = (bottom - top) // rows
            for j, i in enumerate(indices):
                row, col = divmod(j, cols)
                if indices is secondary and len(indices) < cols:
                    col += cols - len(indices)
                boxes[i] = [margin + col*cell_w + margin//2, top + row*cell_h + margin//2,
                            cell_w-margin, cell_h-margin]
    for i, box in enumerate(boxes):
        if not isinstance(box, (list, tuple)) or len(box) != 4 or any(type(v) is not int for v in box):
            raise ValueError('Boxes must contain four integer pixel coordinates')
        x, y, w, h = box
        if min(x, y) < 0 or min(w, h) < 100 or x+w > width or y+h > height:
            raise ValueError('Box too small or outside canvas: ' + str(i))
        for bx, by, bw, bh in boxes[:i]:
            if x < bx+bw and bx < x+w and y < by+bh and by < y+h:
                raise ValueError('Molecule boxes overlap')
    return boxes


def font_at(size):
    for name in ('DejaVuSans.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                 '/System/Library/Fonts/Supplemental/Arial.ttf'):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default(size=size)


def render(config, photo_path, output):
    config = resolve(config)
    w = number(config, 'width', 2400, 512, 8192, True)
    h = number(config, 'height', 3400, 512, 8192, True)
    if w*h > 32_000_000:
        raise ValueError('Canvas exceeds 32 megapixels')
    bond = number(config, 'bond_width', 10, 1, 24)
    brightness = number(config, 'brightness', 1.65, .1, 4)
    lift = number(config, 'fill_lift', .30, 0, 1)
    opacity = number(config, 'background_opacity', .07, 0, 1)
    mode = config.get('mode', 'photo-fill')
    if mode not in ('photo-fill', 'outline'):
        raise ValueError('mode must be photo-fill or outline')
    labels = config.get('labels', True)
    if not isinstance(labels, bool):
        raise ValueError('labels must be boolean')
    boxes = boxes_for(config, w, h)
    out = Path(output)
    out.mkdir(parents=True, exist_ok=False)
    mask = Image.new('L', (w,h), 0)
    for item, (x,y,bw,bh) in zip(config['compounds'], boxes):
        label_h = max(40, int(h*.021)) if labels else 0
        draw_h = bh-label_h
        mol = Chem.MolFromSmiles(item['smiles'])
        rdDepictor.Compute2DCoords(mol)
        drawer = rdMolDraw2D.MolDraw2DCairo(bw, draw_h)
        opts = drawer.drawOptions()
        opts.setBackgroundColour((0,0,0))
        opts.setAtomPalette({i:(1,1,1) for i in range(1,119)})
        opts.bondLineWidth = bond
        opts.minFontSize = max(12, int(w*.011))
        opts.maxFontSize = max(24, int(w*.020))
        opts.padding = .10
        rdMolDraw2D.PrepareAndDrawMolecule(drawer, mol)
        drawer.FinishDrawing()
        tile = Image.open(io.BytesIO(drawer.GetDrawingText())).convert('L')
        tile.load()
        if 'box' in item:
            tile = tile.crop(tile.getbbox())
            tile.thumbnail((bw-12, draw_h-12), Image.Resampling.LANCZOS)
        mask.paste(tile,(x+(bw-tile.width)//2,y+(draw_h-tile.height)//2))
        if labels:
            draw = ImageDraw.Draw(mask)
            size = max(12, int(w*.012))
            label = item['name'].upper()
            while size > 8 and draw.textlength(label,font=font_at(size)) > bw-8:
                size -= 1
            if draw.textlength(label,font=font_at(size)) > bw-8:
                raise ValueError('Caption too long for its box: ' + item['name'])
            draw.text((x+bw//2,y+bh-label_h//2),label,font=font_at(size),fill=255,anchor='mm')
    if photo_path:
        with Image.open(photo_path) as src:
            src.load()
            photo = ImageOps.fit(ImageOps.exif_transpose(src).convert('RGB'),(w,h),method=Image.Resampling.LANCZOS)
        fill = Image.blend(ImageEnhance.Brightness(photo).enhance(brightness),Image.new('RGB',(w,h),(205,213,217)),lift)
        background = Image.blend(Image.new('RGB',(w,h),(13,16,18)),photo,opacity)
    else:
        fill = Image.new('RGB',(w,h),'white')
        background = Image.new('RGB',(w,h),(13,16,18))
    if mode == 'outline':
        fill = Image.new('RGB',(w,h),'white')
    overlay = fill.convert('RGBA')
    overlay.putalpha(mask)
    background.paste(fill,(0,0),mask)
    title = config.get('secondary_title', '')
    if title and not any('box' in item for item in config['compounds']) and any(item.get('group') == 'secondary' for item in config['compounds']) and any(item.get('group','main') == 'main' for item in config['compounds']):
        ImageDraw.Draw(background).text((w*.97,h*.8),str(title),font=font_at(max(12,int(w*.01))),fill=(160,170,175),anchor='rt')
    preview = background.copy()
    preview.thumbnail((1200,1200),Image.Resampling.LANCZOS)
    checks = {}
    for name, image in [('collage.png',background),('overlay.png',overlay),('mask.png',mask),('preview.png',preview)]:
        checks[name] = save_image(out/name,image)
    config['rendered_boxes'] = boxes
    write_json(out/'resolved.json',config)
    write_json(out/'validation.json',checks)
    return checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command',required=True)
    res = sub.add_parser('resolve')
    res.add_argument('--input',required=True,type=Path)
    res.add_argument('--output',required=True,type=Path)
    ren = sub.add_parser('render')
    ren.add_argument('--input',required=True,type=Path)
    ren.add_argument('--photo',type=Path)
    ren.add_argument('--out',required=True,type=Path)
    val = sub.add_parser('validate')
    val.add_argument('files',nargs='+',type=Path)
    args = parser.parse_args()
    if args.command == 'validate':
        print(json.dumps({str(p):validate_image(p) for p in args.files},indent=2))
    else:
        config = json.loads(args.input.read_text())
        if args.command == 'resolve':
            if args.output.exists():
                raise FileExistsError('Use a new output filename')
            write_json(args.output,resolve(config,online=True))
            print(args.output)
        else:
            print(json.dumps(render(config,args.photo,args.out),indent=2))

if __name__ == '__main__':
    main()
