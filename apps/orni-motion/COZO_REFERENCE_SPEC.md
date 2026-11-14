# COZO / CELVANI — visual fidelity contract v1

Source of truth: two user-supplied reference images in the 2026-11-14 conversation. They are **not** licensed external assets and are not stored in GitHub. This text describes what to reproduce. Do not claim that the current primitive rig achieves it.

## Character identity — reference 1

- Height reference: 6 ft 2 in / 188 cm; lean-athletic mannequin, broad silhouette comes from clothes rather than anatomy.
- Head: matte light-gray faceted smooth-poly shell, elongated tapered chin, subtle forehead planes, two deep black oval eye sockets; no nose or visible mouth. Black/white quartered crash-test circle inset on right temple.
- Hands: pale-gray articulated mannequin fingers, not skin-tone human hands.
- Signature outfit: cropped oversized black hooded down puffer with wide horizontal baffles, soft shiny textile, high neck, small CELVANI chest mark; extremely wide light-wash faded blue jeans with folds pooling over chunky matte-black lug boots.
- Branding: CELVANI wordmark, subtle black-on-black garment trims, CELVANI neck/waist tag, circular C zipper pull where visible.
- Character consistency: identical head geometry, eye position, emblem, body proportions, puffer silhouette, denim width and boots across all camera angles.
- Approved poses: seated with hands together, standing relaxed, slow walk. Keep expression deadpan through body language and camera timing.
- Turnaround: front, three-quarter, side, rear. A single cube torso/head is a **placeholder** and not final.

## Scene and camera — reference 2

Location: minimalist premium CELVANI boutique at night, cool gray polished concrete walls and floor, dark metal clothing racks carrying black/gray garments, overhead fluorescent strips, CELVANI wall logo, glass storefront with dark street beyond. Manager: low-poly adult man, short dark hair, dark charcoal crewneck sweater over collared shirt.

Timeline (15 seconds):
- 00:00–00:03: over-the-manager-shoulder two-shot, manager seated at wood desk, COZO seated opposite, visible boutique logo and racks. Dialogue/subtitle: “Manager: Why do you want to work here?”
- 00:03–00:07: close-up COZO head/upper puffer, temple emblem visible. Subtitle “COZO: I don’t.” Dry delivery; awkward pause.
- 00:07–00:11: medium full-body COZO rises from chair, desk and manager foreground left, jeans and boots visible.
- 00:11–00:14: rear wide shot COZO walks toward glass storefront; nighttime city beyond.
- 00:14–00:15: manager reaction and cut to CELVANI® / 001 title card. Final second may split into reaction and title.

Render: 9:16 vertical, 15 seconds, PS2/PSX-inspired low-poly cinematic *with textured surfaces*, not unlit primitives. Muted gray-black-blue palette, soft directional contrast, restrained camera cuts. Keep titles/subtitles readable in mobile safe area.

## Acceptance criteria

1. Character face and wardrobe visibly match reference 1 in at least front, side and rear test frames.
2. Boutique layout, glass exit, wall logo, manager and over-shoulder compositions match reference 2.
3. Exactly 15 seconds, 9:16, stable character identity across all shots.
4. Standing and walking use articulated joints and plausible foot contact, not sliding root motion.
5. Dialogue audio and subtitles aligned to corresponding scenes.
6. Deliver verified playable MP4, preview frames and editable .blend.
7. Automated output validation and manual visual comparison required before marking APPROVED.

## Current implementation gaps

The present COZO Blender scripts are procedural **blockouts**. They lack a production head mesh, textile detail, proper articulated fingers, convincing walk cycle, glass exit, finished manager, accurate logo asset, synced audio and validated finished video. The reference images are not being embedded or reproduced as textures automatically.
