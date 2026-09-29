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

Recommended provenance fields are:

```yaml
manifest_version: 1
schema:
  release: "3.0"
  revision: 7
  revised: "2020-05-18"
codelists:
  issue: 73
sources:
  authoritative:
    authority: EDItEUR
    location: <recorded distribution URL>
    retrieved_at: <date>
  downstream_verification:
    authority: Bokbasen
    location: <recorded production schema URL>
    file: ONIX_BookProduct_3.0_reference.xsd
    sha256: <checksum when retrieved>
files:
  - path: ONIX_BookProduct_3.0_reference.xsd
    sha256: <checksum>
```

A downstream checksum may corroborate the vendored bytes, but cannot replace authoritative provenance. `manifest_version: 1` identifies this contract; incompatible manifest-format changes must increment the version and require explicit verifier support. If authoritative and downstream copies are both retrieved, record whether their SHA-256 values are identical; never silently substitute one for the other.

## Verified schema identity

The Deutsche Nationalbibliothek's 2026 ONIX 3.0 metadata documentation identifies the reference schema as `ONIX_BookProduct_3.0_reference.xsd`, ONIX International Book Product Information Message Schema, Release 3.0 Revision 7, revised 2020-05-18, and attributes it to EDItEUR. DNB also points implementers to EDItEUR's Release 3.0 downloads.

DNB additionally identifies EDItEUR's Release 3.0 Downloads page (`/93/Release-3.0-Downloads/`) as the distribution location for the specification and related ONIX 3.0 material.

This verifies the expected base-schema identity, but not the bytes of a local copy. The vendored file must therefore still be obtained through an authoritative distribution path and checksum-recorded before M3 qualification can claim XSD compliance.

## Source policy

EDItEUR is the standards authority. A downstream distributor such as Bokbasen may be used to confirm which EDItEUR schema is in current production use, but a downstream copy must not be described as authored or published by EDItEUR unless its provenance is established.

The schema files are standards material and are not covered by the repository's MIT software license. Preserve EDItEUR notices and applicable terms.

## Norwegian production endpoint

Bokbasen's public ONIX export documentation shows production messages with `xsi:schemaLocation` pointing to `https://api.boknett.no/schema/ONIX_BookProduct_3.0_reference.xsd`. This is useful independent evidence of the schema entry point used in the Norwegian book metadata ecosystem.

Treat this as a downstream production copy, not as the standards authority. It may be used to compare a candidate EDItEUR bundle byte-for-byte or structurally, but Ploos must not relabel Bokbasen-hosted bytes as an EDItEUR distribution.

## Qualification

Production ONIX qualification consists of:

1. verify the pinned bundle against `MANIFEST.yaml`;
2. generate ONIX;
3. run the internal structural checks;
4. validate the generated XML with the pinned XSD entry point;
5. retain the schema identity/checksums with qualification evidence.

M3 is not complete until this sequence passes in CI using a reviewed bundle.
