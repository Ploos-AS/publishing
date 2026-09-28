# Publication lifecycle and revisions

Ploos Publishing separates a bibliographic **edition** from a production **revision**.

## Lifecycle

Allowed states are:

`draft -> candidate -> qualified -> published -> archived`

A publication may also move from `candidate` or `qualified` back to `draft` when corrections are required. A published publication is immutable as a released product; corrections create a new revision, and material changes create a new edition.

## Edition vs revision

- **Edition** identifies a materially distinct bibliographic edition. A new edition may require new product ISBNs.
- **Revision** identifies rebuilds/corrections within the same edition when the bibliographic product remains the same.
- Git tags/releases record software-style provenance; they do not replace edition or ISBN identity.

Metadata records both values so release manifests and store packages can be traced to the exact production revision.

## Rules

`edition.number` and `edition.revision` are positive integers. `edition.year` is the publication year. `lifecycle.status` must be one of the allowed states.

Only `qualified` metadata should enter final store packaging. Transition to `published` records that the qualified product has actually been released. `archived` is terminal for that revision.
