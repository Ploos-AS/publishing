# PLOOS-PROJECT-1

Status: **Ploos AS project standard v1**

This document defines the common repository and lifecycle contract for Ploos AS projects. It is capability-based: projects implement only the parts that apply to them, while using shared infrastructure instead of copying it.

## Principles

1. The project repository owns its domain sources, examples, tests and project-specific documentation.
2. `Ploos-AS/hardware-ci` owns reusable qualification workflows for HDL, FPGA and hardware-related verification.
3. `Ploos-AS/publishing` owns reusable publishing policy, metadata, validation and production conventions.
4. Shared infrastructure is consumed through stable major-version references such as `@v1`.
5. `main` is canonical in each project. Forgejo may be the primary development forge where configured; public mirrors must not redefine the project contract.
6. Qualification is fail-closed: missing required evidence is a failure, not an implicit pass.
7. Generated artifacts must be reproducible from version-controlled source and declared tooling.
8. Proprietary, restricted or unsafe payloads are never added merely to make CI self-contained.

## Standard lifecycle

```text
source -> validate -> test -> qualify -> build -> publish -> release
```

Stages may be omitted only when the corresponding capability does not apply.

### source

Canonical human-maintained project material: course text, software, HDL, hardware design files, examples and metadata.

### validate

Structural and semantic validation before expensive build or qualification work.

### test

Project-local deterministic tests. These remain owned by the project repository.

### qualify

Reusable evidence-producing checks. Hardware/HDL/FPGA projects use stable workflows from `Ploos-AS/hardware-ci`.

### build

Produce reproducible project outputs from canonical sources.

### publish

Publishing-capable projects use Ploos Publishing conventions to produce declared first-class formats.

### release

A release is made only from a revision whose required tests, qualification and publication checks pass.

## Capability declaration

A project may implement any combination of these capabilities:

- `docs`: documentation/course sources
- `i18n`: parallel language editions
- `software`: executable software
- `simulator`: deterministic simulator/reference model
- `hdl`: synthesizable HDL
- `hardware`: PCB/electronics/manufacturing sources
- `fpga`: FPGA target
- `publishing`: publication outputs
- `website`: generated web edition

Capabilities describe requirements; they do not force empty directories.

## Recommended repository layout

```text
project/
├── README.md
├── ROADMAP.md
├── LICENSES.md
├── docs/
│   ├── no/
│   └── en/
├── exercises/          # if applicable
├── labs/               # if applicable
├── simulator/          # if applicable
├── software/           # if applicable
├── hdl/                # if applicable
├── hardware/           # if applicable
├── publishing/         # project metadata/config only
└── .github/workflows/
    ├── qualification.yml
    └── publishing.yml
```

Existing repositories do not need cosmetic directory migrations merely to conform. Semantic compatibility is more important than identical layout.

## Qualification contract

Projects must keep project-specific tests local. Reusable qualification machinery belongs in `Ploos-AS/hardware-ci`.

Consumers:

```yaml
jobs:
  hdl:
    uses: Ploos-AS/hardware-ci/.github/workflows/hdl.yml@v1
```

Production projects must use a qualified stable major tag, not `@main`.

A qualification pass means the checks configured by that workflow passed for the exact project revision. It must not be described as proving properties that were not tested.

## Publishing contract

Publishing-capable projects keep canonical content in the project repository and use `Ploos-AS/publishing` for common policy and production conventions.

Where applicable, Ploos course/book projects treat these as first-class outputs:

- Web/HTML
- EPUB
- Kindle-friendly ebook
- PDF

Norwegian (`nb`) is normally primary and English (`en`) parallel when the project declares both languages.

Project repositories should contain only project-specific publishing metadata/configuration. Generic templates, schemas and reusable build logic belong in `Ploos-AS/publishing`.

## Licensing

Each repository must document license applicability in `LICENSES.md` when more than one license class is present.

Ploos defaults:

- software/source code: MIT unless upstream obligations require otherwise
- hardware/PCB/HDL: CERN-OHL-P-2.0
- course/documentation material: an appropriate Creative Commons license, normally the project-declared Ploos documentation license

Third-party licenses always take precedence for their respective material.

## Versioning and compatibility

The identifier `PLOOS-PROJECT-1` is the v1 compatibility contract.

Compatible clarifications may be added without changing the identifier. A change that makes a previously conforming project semantically incompatible requires a new major contract, for example `PLOOS-PROJECT-2`.

Shared workflow consumers should pin stable major aliases (`@v1`) after the underlying release has been qualified. Immutable release tags may additionally be used where exact reproducibility is required.

## Adoption

A project adopts PLOOS-PROJECT-1 by:

1. declaring the standard in its README or project metadata;
2. identifying applicable capabilities;
3. using stable shared workflows for applicable qualification/publishing tasks;
4. documenting intentional deviations;
5. requiring green applicable gates before a release.

Adoption must improve consistency without forcing irrelevant machinery into a project.
