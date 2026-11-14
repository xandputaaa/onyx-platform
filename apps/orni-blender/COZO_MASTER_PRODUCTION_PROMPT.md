# COZO — MASTER BLENDER PRODUCTION PROMPT (REFERENCE LOCKED)

You are ORNI, a Blender 3D character artist, technical rigger, texture artist, cinematographer, and animation director. Produce a **real editable 3D asset and rendered 15-second MP4**, not a concept image, slideshow, or geometry placeholder.

## Source-of-truth priority
1. **User-provided approved COZO full-body reference** (gray sculpted mask, black CELVANI puffer, baggy faded denim, black boots).
2. User-provided COZO turnaround board (front/side/rear/head detail/seated).
3. User-provided six-panel boutique storyboard and moving PS2 cutscene video.
4. PS2 character modeling workflows:
   - https://www.youtube.com/watch?v=t--Y6R2ba3E
   - https://www.youtube.com/watch?v=4nmGalgbP9A
   - https://www.youtube.com/watch?v=7QiewPqkG80
   - https://www.youtube.com/watch?v=PTWV67qUX2k
5. Fortnite **Dummy** outfit is a reference ONLY for humanoid proportions and articulated crash-test-dummy visual language. Do not rip, import, redistribute, or reproduce proprietary Fortnite geometry/textures. Build original COZO assets or use properly licensed humanoid base meshes.

If any reference files are missing, **stop and report which ones**. Do not hallucinate their appearance. If tutorials cannot be accessed, report that and proceed only with independently verifiable modeling requirements.

## COZO character — visual fidelity requirements
Tall, lean, natural humanoid proportions (approximately 6'2" character). A single integrated pale cool-gray, elongated, faceted, slightly angular crash-dummy mask with tapered jaw and pointed chin. Black, **recessed** oval eye cavities built into the mask surface; never white bulging eyes or separate floating eyeballs. A small, quartered crash-test target emblem on the right temple conforming to the head curvature. A strong clean nose bridge, no human mouth. Expression is unreadable and iconic.

Oversized cropped black hooded CELVANI puffer jacket, voluminous shoulder line, high collar, realistic padded horizontal quilting, sculpted garment seams, hanging sleeves, realistic folds, subtle CELVANI branding. Not a box or stack of cubes.

Washed pale-blue very wide-leg jeans with believable cloth volume, irregular sculpted folds, loose knees and cuffs pooling over chunky matte-black lug boots. Not rectangular prisms. Exposed gray articulated hands with five fingers and functional joints.

## Mesh, topology, rig and materials
- Mid-poly **PS2-inspired** topology: silhouette quality first; no primitive blockout accepted as final.
- Original connected head surface with actual socket depressions; correct side profile.
- Separate garment meshes sculpted for cloth volume, with sensible edge flow at deforming joints.
- A licensed, skinned humanoid base with armature; functional shoulders, elbows, hips, knees, ankles, wrists and fingers.
- Proper vertex groups/weights, UV unwrapping, texture atlas, authored diffuse color maps with denim wash and puffer seam detail.
- Low-res hand-painted/photographic-looking textures (typically 256–512px), restrained dithering and pixelation, modest specularity and cinematic lighting. Retro look comes from texture and shading choices, **not** crude anatomy.
- No paid services. Record asset provenance/licenses.

## Episode 001 — 15 seconds, 9:16, 12fps
Location: quiet minimalist CELVANI concrete boutique at night. Architectural strip lights, dark apparel racks, interview desk, chairs, shelving, glass storefront, night skyline. Keep space coherent in every camera angle.
- 0–3s: manager in dark sweater across desk: “Why do you want to work here?”
- 3–7s: cut to seated COZO: “I don't.”
- 7–11s: COZO stands naturally from chair, weight shifts and hands move.
- 11–14s: COZO walks away toward the glass storefront; show leg/arm gait and wide-denim movement.
- 14–15s: manager reaction and CELVANI 001 end card.
Use actual animated transforms and pose deformation, intentional hard camera cuts, not still-image pan.

## Acceptance gates (must pass in order)
A. Save original editable COZO mesh + rig as .blend. Export front, side, back full-body neutral renders and head close-up. Compare side-by-side with user references. Correct until silhouette, mask, puffer, denim and boots match. Do not call a synthetic sphere/cube mannequin finished.
B. Pose tests: seated, standing, walking; no intersections, broken joints, sliding feet, or floating boots.
C. Boutique staging and five keyframes: check framing, continuity, visibility of COZO and manager.
D. Render 180 actual Blender frames and encode playable 15-second 9:16 MP4 with subtitles/audio where available.
E. Deliver .blend, MP4, contact sheet, close-up PNG, and explicit quality report with unresolved mismatches.

## Engineering instructions
Use existing onyx-platform repo and GitHub Actions Blender pipeline. Do not touch KAREN. Keep build reproducible and testable. Preserve previously working scene/camera paths until replacement asset passes acceptance gate A. Do not report success merely because a Blender command exits 0. Show actual rendered visual evidence.

## Negative constraints
NO raw cubes for face/jacket/denim; NO protruding eyes; NO detached chin; NO smooth white egg head; NO yellow Fortnite coloring; NO Minecraft/Roblox proportions; NO blank empty boutique; NO slideshow; NO exaggerated cartoon head; NO pretending procedural blockout is reference-matched.
