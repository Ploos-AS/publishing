# Pinned ONIX schema bundle

Ploos Publishing validates ONIX with a local schema bundle. Network downloads are not performed during qualification.

## Components

The bundle is treated as two independently versioned inputs:

1. **ONIX 3.0 base schema** — Release 3.0 Revision 7 (`ONIX_BookProduct_3.0_reference.xsd`).
2. **ONIX codelist schema module** — Issue 73 for the current Norwegian baseline, subject to provenance verification against the authoritative EDItEUR bundle.

For the current Norwegian publishing baseline, the reviewed codelist issue is **Issue 73**, published by Bokbasen on 2026-04-22. Bokbasen states that ONIX codelists are updated four times per year. This records the Norwegian integration baseline; the vendored schema module must still have authoritative EDItEUR provenance.

The base schema revision and codelist issue must both be recorded. Updating a codelist module is therefore an explicit publishing-toolchain change even when the ONIX 3.0 base schema revision is unchanged.

## Vendor layout

Expected layout:

```text
vendor/onix/
  MANIFEST.yaml
  ONIX_BookProduct_3.0_reference.xsd
  ONIX_BookProduct_CodeLists.xsd
  ONIX_XHTML_Subset.xsd
  ONIX_XHTML_Subset_reference.xsd
```

Additional files required by the official bundle may be retained alongside these files.

`MANIFEST.yaml` records the source authority, base schema revision, codelist issue, retrieval date and SHA-256 for every vendored file. Qualification must fail if a recorded checksum does not match.

## Source policy

EDItEUR is the standards authority. A downstream distributor such as Bokbasen may be used to confirm which EDItEUR schema is in current production use, but a downstream copy must not be described as authored or published by EDItEUR unless its provenance is established.

The schema files are standards material and are not covered by the repository's MIT software license. Preserve EDItEUR notices and applicable terms.

## Qualification

Production ONIX qualification consists of:

1. verify the pinned bundle against `MANIFEST.yaml`;
2. generate ONIX;
3. run the internal structural checks;
4. validate the generated XML with the pinned XSD entry point;
5. retain the schema identity/checksums with qualification evidence.

M3 is not complete until this sequence passes in CI using a reviewed bundle.
