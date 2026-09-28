# Norwegian legal deposit tracking

Ploos Publishing tracks Norwegian legal deposit as release provenance.

For publications made generally available in Norway, Nasjonalbiblioteket states that digital publications, including e-books, are subject to legal deposit. Digital documents are deposited by the publisher. The final published version should be deposited; for text documents NB prefers PDF but also accepts EPUB and other formats.

The metadata states whether deposit is required and tracks one of:

- `pending`
- `submitted`
- `confirmed`
- `not_required`

A submitted or confirmed record must identify at least one deposited artifact. The CLI stores its path, size and SHA-256 so the exact deposited revision can be reconstructed.

Example:

```sh
ploos-publish legal-deposit publication.yaml --status submitted \
  --artifact dist/Tallsystemer.pdf --artifact dist/Tallsystemer.epub \
  --method nb-digital --reference "<receipt/reference>" --write
```

The tracker records evidence; it does not itself submit material to Nasjonalbiblioteket. Store receipts or reference identifiers when available.

Official guidance: Nasjonalbiblioteket, Pliktavlevering / Digitale dokument.
