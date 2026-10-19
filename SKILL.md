---
name: molecule-collage
description: Create accurate 2D molecular collages from a substance list and optional photo, including photo-filled bonds, transparent clipping masks, labeled grids, and non-touching custom arrangements. Use for chemical portrait art, medication collages, molecular wallpaper, or reusable molecule overlays; includes PubChem identity resolution, RDKit depiction, visual review, and verified image export.
---

# Molecule Collage

Please make the artwork with the user, preserving their visual intent and chemical identities. You may stop and report a blocker, unresolved identity, or an unproductive iteration instead of inventing a structure or claiming an unfinished render succeeded.

## Establish the composition

Use preferences already supplied. Ask only when a missing answer changes the result:

- Does the photo fill the **bond strokes and atom letters**, or sit beneath solid molecule outlines? These are different effects. Ring interiors remain open in a stroke mask.
- Which substances belong in the main composition, and which belong in a smaller separate group? Preserve the user's grouping; do not infer dosing schedules.
- Keep drug-name captions by default; remove captions when requested, while retaining chemically necessary atom letters, charges, and stereobonds.
- Start with a labeled grid when no layout was specified. Offer a staggered layout when requested. If a subjective direction remains uncertain, show three comparable previews and let the user choose. Do not generate three automatically when one clear draft suffices.

Keep the photo and personal substance list in the task workspace, never in this skill or its repository. Use `assets/example.json` only as a neutral offline demonstration.

## Resolve structures

Translate brands to active ingredients only when the mapping is clear. ER/XR and gels are formulations, not new molecules. Preserve esters and prodrugs: estradiol cypionate is not estradiol; lisdexamfetamine is not amphetamine. Ask about ambiguous names or combination products. Choose parent compound versus salt deliberately and record it in `note`.

Use PubChem isomeric SMILES or user-supplied validated SMILES/CIDs. Never synthesize a SMILES string from a drug name by guessing. The bundled resolver refuses multiple PubChem hits and supports offline records. Inspect its resolved JSON before rendering: name, CID, stereochemistry, disconnected fragments, and source. A valid RDKit parse alone does not establish the correct identity.

## Runtime and commands

Resolve this skill's directory from its installed location; do not assume a specific agent home. Use a Python environment with `rdkit` and `Pillow`. Check the existing runtime before installing packages. If needed, install in a virtual environment with `python -m pip install -r requirements.txt`.

Read [references/configuration.md](references/configuration.md) for inputs and options. Commands below are relative to this skill's directory:

```bash
python scripts/molecule_collage.py resolve --input /absolute/path/input.json --output /absolute/path/resolved.json
python scripts/molecule_collage.py render --input /absolute/path/resolved.json --photo /absolute/path/photo.png --out /absolute/path/draft-01
python scripts/molecule_collage.py validate /absolute/path/draft-01/collage.png /absolute/path/draft-01/preview.png
```

For masks before a photo is available, omit `--photo`. For a pure photo-filled cutout use `overlay.png`; `collage.png` adds a dim photographic background. The renderer uses molecular data and deterministic compositing; never ask an image generator to invent the chemical structures.

If the user requests photo preparation, inspect the original first and use the host's applicable image-editing tools. Preserve the source separately. For pixel-exact cropping, use a deterministic crop when permitted; do not describe a generative recreation as an exact crop. Do not silently add facial reconstruction, smoothing, new grain, or resolution claims. Large exports do not restore detail missing from a small source image.

## Render, inspect, revise

1. Render into a **new output directory** for every version. Wait for the process to finish successfully before viewing, packaging, uploading, or linking any output.
2. Confirm `validation.json` exists and every image passed full decoding. The script writes atomically, checks PNG integrity and complete decoding, and records dimensions and SHA-256 hashes. Never enable `LOAD_TRUNCATED_IMAGES` to pass validation.
3. Open the whole preview and inspect top, middle, and bottom. Inspect full-size crops when atom letters or stereobonds are hard to judge. Check identities/count, grouping, clipping, touching structures, caption readability, dark photo regions, and the requested effect.
4. Fix the specific issue and render a new version. Adjust bond width, photo brightness, fill lift, spacing, or caption contrast independently. Thick bonds must not close double-bond gaps or hide stereochemistry.
5. If layout is custom, each molecule has a separate bounding rectangle. The script rejects overlapping or out-of-canvas rectangles. Nest silhouettes by arranging tight boxes with visible gaps; do not connect separate molecules or claim pixel-level packing from a plain grid.
6. Stop once the requested result is sound. If several reasonable visual directions remain, show three labeled variants at the same scale. If useful progress stalls, explain the blocker and ask for a preference rather than looping indefinitely.

## Deliver and recover

Deliver a visible preview and the full-resolution collage. Offer the transparent overlay, grayscale mask, and resolved source/configuration when useful. Persist through the host's file mechanism if available. Keep medical details out of filenames and metadata unless requested; `resolved.json` itself contains the user's compound list and should only accompany their own deliverable.

If a download appears cut off, first fully decode the local file. If it fails, regenerate from the saved inputs into a new directory and validate again. If local bytes are valid, resend under a fresh filename; compare hashes if available. Do not blame a network or server without evidence. When packaging, wait for all writers, then read and fully decode every archived image—not merely the ZIP CRC.

For alt text, describe the photo, visual treatment, layout, and the user's intended meaning. Do not infer identities, diagnoses, or medication use from appearance. Do not publish the artwork or its personal inputs as part of publishing this reusable skill.
