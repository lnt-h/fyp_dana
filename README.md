# Gonarra

<p align="center">
  <img src="apps/mobile/assets/brand/gonarra-app-icon.svg" width="72" alt="Gonarra" />
</p>

Gonarra is the working name for a bilingual Vietnamese/English AI itinerary planner for travel in Vietnam. The planned launch supports Hà Nội, Thành phố Hồ Chí Minh, Đà Nẵng, Hội An, and Huế with editable one-to-three-day itineraries shown as a timeline and map.

Built with React Native, Expo, TypeScript, and Expo Router. The current implemented slice includes branded onboarding, preview discovery UI, and Clerk-backed authentication with profile and travel preferences. The AI planner, bilingual city catalog, routing backend, and Local Guide are not implemented yet.

## Getting started

```bash
cd apps/mobile
npm ci
# Authenticate the CLI, then restore keys for the existing linked Clerk app:
npx -y clerk@latest auth login
npx -y clerk@latest env pull
npx expo start --go
```

Press `a` for Android, `i` for iOS, or `w` for web. To create a native development build, run `npm run android` or `npm run ios`.

## Documentation

Start with the [business requirements](docs/BRD.md) and [product requirements](docs/PRD.md). The [documentation index](docs/README.md) links use cases, user stories, database design, engineering contracts and release evidence requirements.

The [historical design reference](design/README.md) records earlier visual review passes.
