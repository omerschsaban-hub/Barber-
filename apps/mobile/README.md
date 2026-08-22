# Fabrient Mobile

Native Android/iOS client for Fabrient, built with React Native and Expo Router.

## Run locally

From `apps/mobile`:

```bash
npm install
npx expo start
```

Set `EXPO_PUBLIC_SUPABASE_URL` and `EXPO_PUBLIC_SUPABASE_ANON_KEY` for Supabase-backed features.

The mobile client intentionally reuses the existing Fabrient backend and engineering APIs rather than duplicating engineering logic. Expo Router provides native navigation, deep linking and a shared route model for native/web clients. 
