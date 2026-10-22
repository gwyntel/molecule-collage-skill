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

## Install with Vercel Skills CLI

This repository is a single-skill package. The root `SKILL.md` contains the required
Agent Skills frontmatter (`name` and `description`), so no directory restructuring
is needed. Canonical source: https://github.com/gwyntel/molecule-collage-skill

Install globally for Hermes Agent:

```bash
npx skills add gwyntel/molecule-collage-skill --skill molecule-collage --agent hermes-agent -g -y
```

Claude Code and Codex are supported by current Vercel Skills CLI releases; replace `hermes-agent` with `claude-code` or `codex` respectively, subject to the installed CLI's supported target list. This distributes instructions/files only, not runtime capabilities. To preview the repository's available skills without installing, run
`npx skills add gwyntel/molecule-collage-skill --list`.

After installation, ask your agent: “Use molecule-collage to make a photo-filled
collage of these substances.” The entry point is [SKILL.md](SKILL.md); the renderer
and references ship alongside it.

### Update

Run `npx skills update molecule-collage -g -y` to update the global installation.
If installed at project scope, run `npx skills update molecule-collage -y` from that
project instead. To reinstall directly from this source, rerun the `skills add`
command above. For a manual Git clone, `git -C YOUR_SKILLS_DIR/molecule-collage
pull --ff-only` updates it.

### Troubleshooting

- **Skill not discovered:** confirm the installed name is `molecule-collage` and
  that your agent supports skills from its configured skill directory. This repo
  intentionally uses root `SKILL.md` discovery; its frontmatter must retain valid
  YAML `name` and `description` fields.
- **Wrong scope or agent:** specify `-g` for global or omit it for project scope;
  pass the supported agent identifier with `--agent` during installation.
- **Permission errors:** check write access to the selected agent skills directory;
  use project scope when you cannot write to the global directory.
- **Renderer dependency errors:** CLI installation distributes the instructions and
  files, not Python dependencies. Follow “Run the renderer directly” below.

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
