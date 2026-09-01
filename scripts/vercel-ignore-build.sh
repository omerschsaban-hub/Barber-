#!/usr/bin/env bash
set -euo pipefail

# Vercel Ignore Command contract:
# exit 0 => cancel this build; exit 1 => continue.
# Only skip a Vercel build when every changed path is backend/CI/Render-only.
# Anything ambiguous still deploys, preventing accidental stale frontend releases.

if [[ -z "${VERCEL_GIT_PREVIOUS_SHA:-}" ]]; then
  exit 1
fi

base="$VERCEL_GIT_PREVIOUS_SHA"
head="${VERCEL_GIT_COMMIT_SHA:-HEAD}"

if ! changed_output="$(git diff --name-only "$base" "$head" 2>/dev/null)"; then
  # Vercel may restore a cache whose previous commit is no longer present in
  # the checkout.  A missing comparison is ambiguous: deploy rather than
  # cancel and risk serving a stale frontend.
  exit 1
fi
if [[ -z "$changed_output" ]]; then
  exit 0
fi
mapfile -t changed <<<"$changed_output"

if (( ${#changed[@]} == 0 )); then
  exit 0
fi

for path in "${changed[@]}"; do
  case "$path" in
    engineering/*|services/mcp/*|tests/*|.github/*|render.yaml|Dockerfile|docker-compose*.yml|*.md)
      ;;
    *)
      # Frontend or shared/unknown change: keep the Vercel build.
      exit 1
      ;;
  esac
done

# All changes are backend/CI/documentation-only; no frontend rebuild is needed.
exit 0
