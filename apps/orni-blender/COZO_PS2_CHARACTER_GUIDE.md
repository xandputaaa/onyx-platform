# COZO — PS2 character production gates

## Target
Use the user's approved COZO turnaround as the **only visual authority**. Fortnite Dummy is an anatomical/rigging reference, not a model to extract or redistribute. The old procedural character is an animation blockout, **not** an accepted character model.

## Geometry
- One continuous, tapered, pale-gray faceted mask silhouette. Recess black eye cavities into face topology. Never use floating white eyeballs or a detached chin.
- Quartered crash-test emblem on the temple, following the skull curvature.
- Black oversized, cropped CELVANI hooded puffer: distinct body silhouette, sculpted horizontal quilting, raised collar, integrated hood and believable sleeve folds.
- Baggy washed light-blue denim: wide thighs and knees, irregular fold topology, hems stacked over chunky dark boots. No cube legs.
- Five articulated fingers per hand; anatomical shoulder, elbow, knee and ankle deformations.
- Preserve mid-poly shape complexity. The silhouette should read at 360×640 before adding textures.

## PS2 treatment
- Prefer hand-authored UVs and 256–512px diffuse maps, with selective 1024px face/clothing details only where justified.
- Use painted shadow/roughness and low-frequency fabric folds, not untextured primitives or noisy procedural shaders alone.
- Use deliberate hard/soft edge transitions and modest specular highlights. Retro output resolution is a **finishing pass**, not a substitute for good geometry.
- Keep PS2-inspired stylization without claiming hardware-accurate PS2 rendering.

## Rig/import acceptance
- Legally licensed original or CC0 humanoid GLB/GLTF, with a skin modifier, >=15 deform bones, >=1000 skinned vertices.
- Preserve asset provenance and license in the production manifest. The synthetic test fixture is not a usable COZO asset.
- A rigged base is a starting point: custom mask, jacket, denim, hands, and boots still require modeling and weight painting.

## Visual signoff before episode rendering
1. Neutral, front full-body against approved reference.
2. Side and rear silhouette.
3. Head close-up: recessed eyes, no detached face components.
4. Bent-elbow, walking, and seated deformation poses.
5. Only after acceptance: re-render the boutique episode's 15-second cinematic.

## Tutorial study
- https://www.youtube.com/watch?v=t--Y6R2ba3E — PS2-style character modeling
- https://www.youtube.com/watch?v=4nmGalgbP9A — character, clothing, UV and rigging workflow
- https://www.youtube.com/watch?v=7QiewPqkG80 — detailed low-poly workflow
- https://www.youtube.com/watch?v=PTWV67qUX2k — low-poly character modeling and animation

## Current status
Import smoke test passes in GitHub Actions run 43652536932. This is **not** reference-accurate character approval. Do not label the procedural blockout a finished COZO render.
