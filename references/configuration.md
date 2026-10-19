# Configuration and reproducibility

Use UTF-8 JSON. All records belong in `compounds`; each needs a `name` plus either
`smiles`, `cid`, or a resolvable name. Optional `query` overrides the PubChem name
search. `group` is `main` (default) or `secondary`. Optional `note` records the
parent/salt/formulation decision. `source` should be retained for supplied SMILES.

`resolve` writes a new JSON file and refuses to overwrite an existing one. Names
are sent to PubChem only for unresolved records; photos are never uploaded by the
script. PubChem requests run sequentially with bounded retries. Ambiguous results
stop resolution. Inspect `cid`, `smiles`, `formula`, and `fragments` before rendering.
Use CID or curated SMILES to resolve ambiguity, rather than selecting the first hit.

| Key | Default | Meaning |
| --- | --- | --- |
| width, height | 2400, 3400 | Output pixels; 512–8192 per side, at most 32 megapixels |
| columns | 3 | Main grid columns, 1–8 |
| labels | true | Drug-name captions; atom labels always retained |
| mode | photo-fill | `photo-fill` or `outline` |
| bond_width | 10 | RDKit bond stroke pixels, 1–24 |
| brightness | 1.65 | Photo-fill brightness multiplier, 0.1–4 |
| fill_lift | 0.30 | Blend photo fill toward light gray, 0–1 |
| background_opacity | 0.07 | Original photo visible behind molecules, 0–1 |
| secondary_title | empty | Optional group heading, e.g. `OCCASIONAL` |

The photo is center-cropped to fit, never stretched. Prepare a different crop before
rendering when the subject is off-center. Exif orientation is applied. With no photo,
the renderer uses white on transparency over a near-black background.

For custom layouts, every compound must have `box: [x, y, width, height]` in output
pixels. Boxes include caption space if captions are enabled. Leave at least a few
pixels of space. Rendered silhouettes are tightly cropped and centered within the
boxes; aspect ratio is preserved. Boxes must not overlap. Custom layouts take
precedence over automatic grouping, so place secondary records together yourself.
No molecule rotation or reflection is performed by this renderer.

Outputs in a fresh `--out` directory:

- `collage.png`: finished opaque composition.
- `overlay.png`: photo-filled or white structure layer with alpha.
- `mask.png`: white bonds/atom letters/captions on black.
- `preview.png`: PNG preview, longest edge at most 1200 pixels.
- `resolved.json`: exact rendered inputs, normalized identities and source references.
- `validation.json`: dimensions, modes, SHA-256 values, and successful full decode.

The output directory is reserved before rendering and never reused. On failure,
keep it for diagnosis and choose a new directory for retry. `validation.json` is
written last; its absence means the run is incomplete. Test `scripts/test_collage.py`
for offline rendering, invalid layouts, and truncated-PNG rejection.

Primary documentation:
- https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest
- https://www.rdkit.org/docs/source/rdkit.Chem.Draw.rdMolDraw2D.html
- https://pillow.readthedocs.io/en/stable/reference/Image.html
