# Gonarra assets

## Layout

- `brand/`: existing standalone brand vectors. Runtime brand components live in `src/components/brand/BrandMarks.tsx`.
- `images/places/`: shared travel photography used by onboarding and Home; future screens should reuse these files rather than duplicate them.
- `images/onboarding/`: imagery specific to onboarding compositions.
- `images/cities/`: bundled city cover photos (Wikimedia Commons; source, author and licence per file in `images/cities/attribution.json`), used via `src/lib/images/cityImages.ts`. Place photos are not bundled: they come from the API as remote media with attribution.
- `illustrations/registration/`: original abstract registration artwork.
- `illustrations/backgrounds/`: original decorative background vectors.
- Root PNG files: Expo app icons, adaptive icons, splash icon, and favicon. Their paths remain unchanged to preserve app configuration.

Do not create empty font, audio, or icon directories. Add them when approved assets are actually introduced. No new font or icon dependency is required by this organization change.

## Naming and rendering

- Use descriptive lowercase kebab-case filenames. Do not invent an exact location in a filename until it has been verified.
- Keep photography as raster images; do not wrap photos in SVG or embed interface text into images.
- Preserve current image files and crops during organizational changes. Optimize future exports against actual display sizes without upscaling.
- Use static literal `require()` paths for bundled React Native images.
- These standalone SVGs are editable source artwork. The project does not configure an SVG import transformer: do not import `.svg` files as React components or pass them to native `Image` expecting SVG rendering.
- For screen integration, implement their shapes with the existing `react-native-svg` primitives, as the brand components already do. Use theme tokens for runtime colors. Do not add a transformer solely for these two illustrations.
- Keep interactive icons in `src/components/`, with consistent stroke widths and accessible labels on their containing controls.
- The map is decorative, not geographic data. Hide decorative illustrations from accessibility traversal; provide labels for meaningful images at the usage site.
- The registration illustration intentionally contains no photos or text. Compose approved shared photos and native text around it when building the screen.

## Provenance and usage register

Last audited: 2026-10-28. A repository asset is not automatically cleared for publication. `apps/mobile/LICENSE` does not establish third-party media rights.

| Files | Origin currently known | Creator/source URL | Rights and publication status |
| --- | --- | --- | --- |
| `images/places/beach.png` | Existing project asset, moved without changing bytes | Not documented | Unverified; confirm location, source, attribution, and reuse rights |
| `images/places/cham-sculpture.png` | Existing project asset, moved without changing bytes | Not documented | Unverified; confirm source and reuse rights |
| `images/places/city-bridge.png` | Existing project asset, moved without changing bytes | Not documented | Unverified; confirm location, source, and reuse rights |
| `images/places/cyclo.png` | Existing project asset, moved without changing bytes | Not documented | Unverified; confirm source and reuse rights; not a real user avatar |
| `images/places/dragon-bridge.png` | Existing project asset, moved without changing bytes | Not documented | Unverified; confirm source and reuse rights |
| `images/places/linh-ung-pagoda.png` | Existing project asset, moved without changing bytes | Not documented | Unverified; confirm source and reuse rights |
| `images/places/marble-mountains.png` | Existing project asset, moved without changing bytes | Not documented | Unverified; confirm source and reuse rights |
| `images/places/mi-quang.png` | Existing project asset, moved without changing bytes | Not documented | Unverified; confirm source and reuse rights |
| `images/onboarding/planning-hero.png` | Existing project composition, moved without changing bytes | Not documented | Unverified; review constituent media and reuse rights |
| `brand/*.svg` and root app-icon/splash PNGs | Existing project branding | Original authorship not documented here | Confirm ownership and any constituent media rights |
| `illustrations/registration/trip-ready-map.svg` | Original vector geometry authored in this task, informed by supplied registration design | Codex-assisted project artwork, 2026-10-28; no external media embedded | No third-party asset license supplied; project owner reviews final publication |
| `illustrations/backgrounds/auth-wave.svg` | Original vector geometry authored in this task, informed by supplied auth design | Codex-assisted project artwork, 2026-10-28; no external media embedded | No third-party asset license supplied; project owner reviews final publication |

For each approved photograph, record the original source URL, creator, license/permission reference, required attribution, permitted modifications, redistribution/offline rights, reviewer, and review date. Keep private permission evidence outside the public repository. Unknown rights must remain explicitly unknown.

Use the [catalog and media contract](../../../docs/04-design/data/data-model.md) for source, reuse rights, attribution and review of destination images. Do not use generated destination imagery as evidence of a real place.

### Welcome imagery — local Figma review

The Welcome composition now uses a dedicated set from the user-supplied `Tourguide app UI.fig` (exported 2026-10-28), rather than referencing the onboarding images. These are original embedded image bytes, not screen captures. This is a distinct Welcome composition; the local `.fig` does not contain the Welcome/auth PNG screen designs.

| Local file | Embedded image hash | Rights |
| --- | --- | --- |
| `images/welcome/cathedral.png` | `083adb5294f05c97d2ca33556c5c5fcf7a49f9d4` | Original photographer/license not documented |
| `images/welcome/museum-gallery.png` | `429955540d0dd884d1c9c067b4b6193db154a56c` | Original photographer/license not documented |
| `images/welcome/dragon-bridge-detail.png` | `19379f1302a15ecad060489a6540218dc4733699` | Original photographer/license not documented |
