# Authentication design references

- `01-welcome.png`: welcome and entry choices.
- `02-login.png`: email sign-in.
- `03-register-account.png`: account form.
- `04-register-preferences.png`: travel preferences.
- `05-register-complete.png`: completion illustration.

The implementation uses native React Native components and Expo Router. Current routes are `/welcome`, `/login`, and `/register`; registration contains three in-memory steps. Existing onboarding now ends at Welcome.

Intentional differences from the references:

- Social sign-in is omitted until providers are configured.
- Preferences use the four planned categories: Culture, Beach, Food, Nature.
- Authentication is an explicitly labeled UI preview. No network authentication, durable preferences, password recovery, or legal consent collection is implemented.
- Completion opens the existing Home screen as a guest and does not claim an account was created.
- Native status bars and safe areas replace decorative phone chrome.

Form values exist only in component memory. Leaving registration discards them; returning between its steps preserves them. Validation is currently bypassed for UI review; no production password policy has been selected.

## Local `.fig` audit — 2026-10-28

Read the supplied `Tourguide app UI.fig` locally after Figma MCP reached its account tool limit. Its embedded Kiwi schema decodes to 1,058 layer records and 60 image files. No named Welcome/Login/Register screens or corresponding auth copy were found; auth PNG references remain a separate design source.

- Discovery screen: `64:1123` (named Onboarding 2 in Figma; first content slide in the app).
- Discovery lower fade: `230:580`, y=330, height=626 on a 440×956 frame. White alpha stops: 0 at 0, .25 at .12545185, .5 at .27795538, 1 at .5940541. Previous code incorrectly multiplied these by .58.
- Planning lower fade: `242:454`, y=450, height=506. Previous code used y=463.
- Personalized lower fade: `242:461`, y=330, height=626. Same full-white gradient stops.
- Native Expo gradients now render these lower veils without relying on SVG Gaussian filters on mobile. This matches the observed fade stops; it is not an exact reproduction of Figma's 20px layer-blur renderer.
- Existing onboarding copy matches Figma wording. Auth preview explanations were repetitive; reduced to a short UI-preview marker. Welcome supporting copy is shortened.
- Welcome uses a landscape Dragon Bridge hero with a smaller cathedral photo overlapping its corner, instead of the capsule columns used by onboarding. Both photos are dedicated embedded assets. It is not claimed as an exact recreation of the five-photo Welcome PNG, whose individual source photos are absent from this local `.fig`.

### Current preview behavior (supersedes earlier validation notes)

As requested, blank inputs do not block Next or Sign In. Registration goes through all three steps without email, password, or terms validation. Sign In opens Home as a UI preview only; no authentication request occurs. Back, Skip, selection, and show/hide password remain interactive. Production validation and real authentication must be reinstated when a backend is connected.

### Typography and remaining review findings

Onboarding text nodes (including `236:276` and `242:470`) specify Hanken Grotesk Medium at 37px in the 440px frame. The app now bundles Medium and Bold through `@expo-google-fonts/hanken-grotesk` 0.4.3 and `expo-font` 58.0.10, rather than relying on system fonts. Fonts are loaded at the root before screens mount, following the [Expo font-loading guidance](https://docs.expo.dev/develop/user-interface/fonts/). Font provenance: [Google Fonts Hanken Grotesk](https://github.com/google/fonts/tree/main/ofl/hankengrotesk).

The existing Home tab bar still has Home / Explore / AI guide / Trips, while `pland.md` requires Home / Explore / Trips / Saved. This pre-existing product/design conflict is recorded for the Home/navigation implementation; this onboarding/auth review does not silently change those destinations.


## Verification of this review

- TypeScript and Expo exports for Web, iOS, and Android passed.
- In Safari, inspected Welcome/registration at a 390×844 web viewport and onboarding at 360×740.
- Clicked through all three onboarding slides into Welcome.
- Clicked through registration with empty fields and no accepted terms or preferences into Home.
- Corrected compact-screen onboarding title positioning from a fixed bottom offset to the Figma reference baseline (title ends at y=762 of 956).
- Added web accessibility hiding for inactive onboarding slides; only the current slide's copy appears in the accessibility tree.
- Added consistent SVG field icons and a labeled password-visibility icon; removed repeated field labels and repeated legal-link rows.
- Browser viewport checks do not establish native keyboard, safe-area, or physical-device rendering correctness. Those remain device checks.

### Welcome and registration layout fix — 2026-10-28

- Welcome now uses a landscape destination card and inset photo, visually distinct from onboarding 1. Entry actions are unchanged.
- Registration step 2 constrains each interest photo inside an aspect-ratio frame with an absolutely positioned cover image. Native image dimensions no longer expand the grid or overlap adjacent tiles.
- Verified on the running iPhone 18 Pro simulator: two-column grid, selection indicators, Next to step 3, and preserved selections when returning. Inspected the updated Welcome layout. TypeScript check passed.
