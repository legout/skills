---
name: pi-custom-model
description: Register a custom model or provider variant in Pi after the installed model registry cannot resolve an exact provider/model ID. Use when the user explicitly asks to add a Pi model or repair an unresolved saved default.
disable-model-invocation: true
---

# Pi Custom Model

> Adapted from David Ondrej's MIT-licensed [`pi-custom-model`](https://github.com/davidondrej/skills/blob/11dee2ebc2d045806b686ba0b57746f1e3d7e331/skills/ops-and-setup/pi-custom-model/SKILL.md) at commit `11dee2ebc2d045806b686ba0b57746f1e3d7e331`. Current installed Pi help and documentation override this pinned workflow.

This workflow edits user-level Pi configuration. Do not run it implicitly.

## Preflight

Before writing anything:

1. Run `pi --version`, `pi --help`, and `pi --list-models <search>`.
2. Locate and read the installed Pi documentation for models and custom providers. Confirm the current `models.json` schema and reload behavior.
3. Confirm the requested provider/model ID against the provider's current authoritative catalog. Preserve spelling, punctuation, and variant suffixes exactly.
4. Determine whether the provider is built in, needs a `models.json` entry, or requires a custom provider extension for a non-standard API.
5. Check only whether authentication is available through Pi's supported login or environment mechanism. Never print or copy credential values from `auth.json`.
6. Check project settings as well as user settings when the problem occurs only in one repository.

If the installed registry already resolves the exact ID, do not add a duplicate custom model. Diagnose the selected provider, project override, or launch arguments instead.

## Files

The usual user-level files are:

- `~/.pi/agent/models.json` — custom provider/model definitions;
- `~/.pi/agent/settings.json` — default provider, model, and thinking level; and
- `~/.pi/agent/auth.json` — credentials managed by Pi; inspect presence only, not values.

Confirm these paths in the installed documentation before mutation. Back up every existing file you will change, preserve unrelated keys, and parse the result as JSON.

## Register the Model

For a built-in provider, add only the provider/model metadata required by the installed schema. Custom model entries merge with built-in providers; do not copy an API key into `models.json` when Pi already manages that provider's authentication.

Minimal shape, subject to the installed schema:

```json
{
  "providers": {
    "<provider>": {
      "models": [
        {
          "id": "<exact-model-id>",
          "name": "<display-name>"
        }
      ]
    }
  }
}
```

Add fields such as reasoning support, inputs, pricing, context window, token limit, compatibility, API, or base URL only when current provider documentation establishes their values. Do not copy stale metadata from a superficially similar model.

For a provider that is not built in, follow the installed custom-provider documentation. Use environment-variable references or Pi's supported authentication flow; never place a literal secret in a tracked project file.

## Verify Before Changing Defaults

1. Parse `models.json` with an available JSON parser.
2. Trigger the reload mechanism documented by the installed Pi version; current versions reload model configuration automatically when the model selector opens.
3. Run `pi --list-models <exact-id-fragment>` and require the intended provider/model row to appear as available.
4. If it does not appear, stop and fix the definition or authentication. Do not change defaults yet.
5. Only after discovery succeeds, update `defaultProvider` and `defaultModel` in `settings.json` while preserving the user's thinking level and unrelated settings.
6. Start or reload Pi and confirm the selected model in the UI. Run a billed smoke prompt only with the user's approval.

Report backups, changed keys, discovery output, and any unresolved provider or authentication issue. Never claim that an unavailable model was registered successfully.
