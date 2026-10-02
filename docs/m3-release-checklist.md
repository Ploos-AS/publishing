# M3 release checklist

M3 is feature complete and frozen. This checklist closes qualification and release; it does not authorize new features.

## 1. Authoritative ONIX bundle

- [x] Obtain the reviewed ONIX 3.0 schema bundle from EDItEUR.
- [x] Confirm Release 3.0 / Revision 7 identity.
- [x] Confirm Codelists Issue 74 baseline.
- [x] Place the four reviewed XSD files under `vendor/onix/`.
- [x] Record EDItEUR provenance, retrieval date and SHA-256 values in `vendor/onix/MANIFEST.yaml`.
- [x] Verify all four vendored files against the recorded authoritative checksums.

## 2. Local verification

- [x] Run `python scripts/ploos_publish.py onix-schema-verify vendor/onix/MANIFEST.yaml`.
- [x] Generate qualification ONIX.
- [x] Run `python scripts/ploos_publish.py onix-bundle-validate <onix.xml> vendor/onix/MANIFEST.yaml`.
- [x] Enforce SHA-256 integrity before XSD validation.

## 3. CI qualification

- [x] Push the reviewed bundle and manifest.
- [x] Confirm **Validate publishing metadata** passes.
- [x] Confirm **Publishing self-test** passes.
- [x] Confirm the pinned-ONIX-bundle step actually runs.
- [x] Record CI evidence: commit `9576921ba1c5b26f561cb33281fe7b391c45e43c`; metadata run `37042091407` PASS; self-test run `37042091378` PASS.

## 4. Production evidence

- [x] Re-run the reusable publishing workflow for EduNumbers NO and EN against the qualified publishing revision.
- [x] Confirm both publication jobs pass.
- [x] Record artifact IDs, workflow run ID and publishing commit in the M3 qualification document.
- [x] Confirm production metadata uses only ISBNs allocated from the canonical official Ploos AS pool (publisher prefix `978-82-94310`).

## 5. Release

- [x] Update `docs/m3.md` qualification status to PASS only after all gates above pass.
- [x] Update the M3 qualification document with final evidence.
- [ ] Run the repository validation/self-test suite at the release commit.
- [ ] Create the M3 release tag only from the fully qualified commit.
- [ ] Publish release notes identifying the qualified commit and evidence.

## Release rule

A synthetic test bundle proves the validator. It does **not** qualify M3. M3 is qualified only when the canonical validation path has passed in CI using the reviewed authoritative EDItEUR bundle and the production publication evidence has been recorded.
