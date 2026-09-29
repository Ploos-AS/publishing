# M3 release checklist

M3 is feature complete and frozen. This checklist closes qualification and release; it does not authorize new features.

## 1. Authoritative ONIX bundle

- [ ] Obtain the reviewed ONIX 3.0 schema bundle from EDItEUR.
- [ ] Confirm the expected Release 3.0 / Revision 7 identity.
- [ ] Confirm the pinned codelist baseline used by this repository.
- [ ] Place the reviewed files under `vendor/onix/`.
- [ ] Record authoritative source, retrieval date and SHA-256 values in `vendor/onix/MANIFEST.yaml`.
- [ ] Do not use an unreviewed mirror as the authoritative source.

## 2. Local verification

- [ ] Run `python scripts/ploos_publish.py onix-schema-verify vendor/onix/MANIFEST.yaml`.
- [ ] Generate qualification ONIX from a real Ploos publication.
- [ ] Run `python scripts/ploos_publish.py onix-bundle-validate <onix.xml> vendor/onix/MANIFEST.yaml`.
- [ ] Confirm failures occur if a vendored schema file is modified without updating its recorded checksum.

## 3. CI qualification

- [ ] Push the reviewed bundle and manifest.
- [ ] Confirm **Validate publishing metadata** passes.
- [ ] Confirm **Publishing self-test** passes.
- [ ] Confirm the conditional pinned-ONIX-bundle step actually ran; an overall green workflow with that step skipped is not sufficient.
- [ ] Record workflow run ID, commit SHA and relevant job/step result in qualification evidence.

## 4. Production evidence

- [ ] Re-run the reusable publishing workflow for EduNumbers NO and EN against the qualified publishing revision.
- [ ] Confirm both publication jobs pass.
- [ ] Record artifact IDs, workflow run ID and publishing commit in the M3 qualification document.
- [ ] Ensure no ISBN is fabricated while the official Ploos AS ISBN range remains pending.

## 5. Release

- [ ] Update `docs/m3.md` qualification status to PASS only after all gates above pass.
- [ ] Update the M3 qualification document with final evidence.
- [ ] Run the repository validation/self-test suite at the release commit.
- [ ] Create the M3 release tag only from the fully qualified commit.
- [ ] Publish release notes identifying the qualified commit and evidence.

## Release rule

A synthetic test bundle proves the validator. It does **not** qualify M3. M3 is qualified only when the canonical validation path has passed in CI using the reviewed authoritative EDItEUR bundle and the production publication evidence has been recorded.
