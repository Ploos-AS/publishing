# PLOOS-STUDENT-OCI-1

Status: **Ploos AS student environment standard v1**

This standard defines the learner-facing OCI contract for practical Ploos courses. Its goal is that a supported course can be started from a clean machine with only the course checkout and a standard OCI runtime.

`clone -> start student OCI -> learn`

## Requirements

A conforming course:

1. publishes a course-specific student image;
2. uses `/course` as the mounted checkout and working directory;
3. provides `student-env-info` and `student-check`;
4. defaults to `student-check` when the image is run without another command;
5. contains the redistributable compiler/toolchain and utilities required by the supported course path;
6. requires no private Ploos service, credentials or private infrastructure during normal learner use;
7. contains no proprietary/restricted payload merely to make the environment self-contained;
8. works with ordinary OCI semantics and is documented for Docker and Podman;
9. is usable non-interactively by CI;
10. publishes development and release identities without silently changing a released course environment.

## Stable commands

### student-env-info

Reports contract/course identity and important tool versions. It must not modify the checkout.

### student-check

Runs the checks expected to work for a freshly cloned course checkout in the student environment.

## Machine-readable declaration

A conforming repository contains `student-oci.json` with schema version 1. The canonical schema is `standards/student-oci.schema.json` in this repository.

Required semantic values include:

- `contract: PLOOS-STUDENT-OCI-1`
- `workspace: /course`
- stable commands `student-env-info` and `student-check`
- `requires_private_infrastructure: false`
- `restricted_payloads: false`

## Image naming and releases

Recommended image name:

`ghcr.io/ploos-as/<course>-student`

`edge` may identify current main development. `sha-*` identities are immutable revision identities. Published course releases should name a qualified semantic-version tag or immutable digest. A released course must not depend on a mutable tag for reproducibility.

## Qualification

CI should build the student image and execute both stable commands. This ensures the learner path is tested rather than merely maintaining an unused Dockerfile.

A student-OCI pass proves only the declared learner environment. Platform/runtime/hardware projects may have additional qualification levels outside this contract.

## Restricted/platform-owned assets

Redistributable toolchains, emulators and simulators may be included when their licenses permit it. Proprietary ROMs, operating-system media, SDKs, keys and learner-owned assets remain external. Optional labs may document external mounts without weakening the core contract.

## Relationship to PLOOS-PROJECT-1

`student-oci` is an optional capability of PLOOS-PROJECT-1. Courses that declare it adopt this contract. Project repositories own course-specific image composition; shared semantics belong here.

## Compatibility

Compatible clarifications may retain the identifier PLOOS-STUDENT-OCI-1. Breaking semantic changes require a new major identifier.
