# Molecule Collage

An agent skill for turning a substance list and a photograph into molecular art.
RDKit draws the chemical structures; Pillow fills their bonds and atom lettering
with the image. Keep a dim photographic background, export transparent overlays,
or use the grayscale layer as a clipping mask in your editor.

Built from a collaborative art workflow: establish the visual idea, resolve the
chemistry, render, inspect, revise, and verify the entire exported image.

## What it does

- Resolves compound names or PubChem CIDs to isomeric SMILES, with an offline path
  for supplied structures.
- Preserves prodrugs, esters, atom labels, charges, and stereochemistry.
- Supports labeled grids, label-free art, separate secondary groups, and custom
  non-overlapping layout boxes.
- Exports a finished PNG, transparent overlay, mask, preview, and provenance JSON.
- Writes outputs atomically and fully decodes each PNG before marking a run complete.
- Guides the agent through visual inspection and targeted revisions; offers three
  alternatives when a subjective choice needs the user's eye.

## Install as an agent skill

Clone into your agent's skills directory using `molecule-collage` as the folder name:

```bash
git clone https://github.com/gwyntel/molecule-collage-skill YOUR_SKILLS_DIR/molecule-collage
```

For example, `YOUR_SKILLS_DIR` may be `~/.codex/skills` or `~/.hermes/skills`.
Then ask: “Use molecule-collage to make a photo-filled collage of these substances.”
The entry point is [SKILL.md](SKILL.md).

## Run the renderer directly

Python 3.10+ and a supported RDKit wheel are required.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

# Bundled offline example; use a fresh output directory for every version.
python scripts/molecule_collage.py render \
  --input assets/example.json --out output/example-01

# Add your own photograph.
python scripts/molecule_collage.py render \
  --input assets/example.json --photo /path/to/photo.png --out output/photo-01

# Resolve a JSON compound list that contains names or CIDs instead of SMILES.
python scripts/molecule_collage.py resolve \
  --input /path/to/input.json --output /path/to/resolved.json

python scripts/test_collage.py
```

See [configuration](references/configuration.md) for the manifest format and all
settings. Photos stay local to the renderer. Name lookups contact PubChem. Personal
photos and medication lists are not bundled; the example uses caffeine, aspirin,
and ethanol, without making any claims about someone's use.

Rendering is chemical illustration, not a recommendation to take or combine substances.
