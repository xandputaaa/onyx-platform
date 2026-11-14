# COZO Episode 001 — Reference-locked production specification

## Primary user-provided references (2026-11-14)
1. Full-body COZO on warm off-white background: faceted elongated pale gray mask, two black inset oval eyes, black/white quartered round emblem on right temple, no mouth, dark neck, oversized black quilted CELVANI hooded puffer with collar and placket, articulated gray hands, washed wide blue jeans with folds pooling at ankles, black heavy lug boots.
2. CELVANI COZO character turnaround and technical sheet: front, side, back, three-quarter silhouettes; puffer/denim variations; sitting and walking poses; sleeve and zipper branding; head topology. Maintain consistent likeness from every angle.
3. Six-panel CELVANI boutique storyboard: concrete walls, hanging black clothing, suspended strip lights, wood interview desk, glass storefront at night, manager in charcoal sweater. Dialogue and cuts: 0–3 manager asks 'Why do you want to work here?'; 3–7 COZO says 'I don't.'; 7–11 stands; 11–14 walks away; 14–15 manager reaction and CELVANI/001 card.
4. Uploaded PS2-style moving cutscene video: use for motion timing, cinematic camera behavior and character performance; do not substitute pans over stills.

## Visual acceptance gates
- **Silhouette:** match head/hood/puffer/denim/boots outline in front, side and back. The current cube-and-sphere rig is a BLOCKOUT and cannot be declared reference-matched.
- **Face:** one integrated sculpted/mid-poly tapered mask with controlled planes, recessed black oval sockets and exact quartered temple mark; no floating eyes, chin cone or separate primitives.
- **Clothes:** continuous garment meshes, visible quilted baffles with soft rounded volume, seam lines, hood opening, ribbed cuffs, placket, brand mark, zipper, oversized denim folds and stacked cuffs. No cube baffles or rectangular trouser columns.
- **Rig:** armature/skinning, natural seated-to-standing weight transfer and planted-foot walk, hands and manager performance.
- **Materials:** UV mapped fabric, denim and concrete photo/PBR textures with deliberately PS2-era moderate-resolution presentation; material roughness and plausible highlights.
- **Environment:** garment-filled rails, wall CELVANI sign, real-looking desk/clipboard, concrete architecture, fluorescent strip lights, dark exterior through glass.
- **Cameras:** first shot must show manager foreground and COZO across table; close-up mask, medium rise, rear exit, manager reaction, end card. Check framing at each beat.
- **Release:** render a 3-second hero shot first, compare side-by-side against provided images; do not spend compute on full 15-second render until silhouette/material/lighting pass. Then full render with H.264/AAC and visual inspection. Passing Blender CI alone is insufficient.

## Verified external research and learning references
- PS2 character modeling workflow: https://www.youtube.com/watch?v=t--Y6R2ba3E (mid-poly silhouette, UV painting and texture constraints)
- PS2 Blender character workflow: https://www.youtube.com/watch?v=4nmGalgbP9A (reference, base mesh, clothing, UV, textures, rigging)
- Poly Haven free CC0 PBR textures and HDRIs: https://polyhaven.com/
- ambientCG CC0 textures: https://ambientcg.com/
- Blender free procedural humanoid motion: https://extensions.blender.org/add-ons/moveset/ (check compatibility before adoption)
- Quaternius free animation library: check asset-specific license before importing.

## Practical limitation
Reference JPGs are visual references, **not** rigged 3D assets. Matching their sculpted geometry, UVs, cloth and animation requires creating or acquiring properly licensed meshes. Procedural blockout refinement is not equivalent to an exact likeness. No new paid services or assets; no changes to KAREN.
