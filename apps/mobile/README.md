# Fabrient Mobile

Native Android/iOS client for Fabrient, built with React Native and Expo Router.

## Run locally

From `apps/mobile`:

```bash
npm install
npx expo start
```

Configure the mobile client with the public Fabrient API/base URL required by the current deployment. Database access must go through the authenticated Fabrient API; the mobile client must not connect directly to PostgreSQL with privileged credentials.

The production database is PostgreSQL. Supabase is not the target database architecture.
