# Accessibility reporting

`ploos-publish accessibility-report` creates a machine-readable JSON report for an EPUB publication.

Example:

```sh
ploos-publish accessibility-report publication.yaml --epub dist/Tallsystemer.epub --language nb -o dist/accessibility-nb.json
```

Status is `PASS`, `WARN`, or `FAIL`. Structural/accessibility errors cause FAIL; non-critical findings such as missing language metadata, missing image alt attributes, or heading-level jumps are represented as warnings where the internal QA classifies them that way.

The report records project/work identity, language, title, edition/revision, artifact SHA-256, issue counts and detailed checks. It is intended to be archived with release provenance.

This is automated internal QA, not a claim of complete WCAG or EPUB Accessibility conformance. Manual review and future dedicated accessibility tooling can supplement the report.
