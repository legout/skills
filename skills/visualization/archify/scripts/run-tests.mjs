import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const repositoryOnly = new Set([
  "architecture-delta.test.mjs",
  "automatic-port-spread.test.mjs",
  "brand-marks.test.mjs",
  "checkout-line-endings.test.mjs",
  "clean-skill-staging.test.mjs",
  "community-proof-intake.test.mjs",
  "cursor-onboarding.test.mjs",
  "gallery.test.mjs",
  "generated-artifact-xml.test.mjs",
  "guide-page.test.mjs",
  "landing.test.mjs",
  "ordinary-model-floor.test.mjs",
  "preview-contract.test.mjs",
  "proof-aperture.test.mjs",
  "reach-share-card.test.mjs",
  "readme-showcase.test.mjs",
  "real-repository-proof.test.mjs",
  "release-identity.test.mjs",
  "release-package-gates.test.mjs",
  "repository-language-metadata.test.mjs",
  "route-share-card.test.mjs",
  "share-card-export.test.mjs",
  "site-language-continuity.test.mjs",
  "skill-metadata.test.mjs",
  "stable-update-manifest.test.mjs",
  "start-page.test.mjs",
]);

const tests = fs
  .readdirSync(path.join(root, "test"))
  .filter((name) => name.endsWith(".test.mjs") && !repositoryOnly.has(name))
  .sort()
  .map((name) => path.join("test", name));

const result = spawnSync(process.execPath, ["--test", ...tests], {
  cwd: root,
  stdio: "inherit",
  env: { ...process.env, CI: process.env.CI ?? "1" },
});

process.exit(result.status ?? 1);
