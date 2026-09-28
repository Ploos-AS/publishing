# Distribution packaging

`ploos-publish package` creates deterministic upload directories per channel and language.

Example:

```sh
ploos-publish package publication.yaml package.yaml --channel amazon --language nb \
  --epub dist/Tallsystemer.epub --cover dist/Tallsystemer-cover.jpg
```

The package contains the selected publication files plus `metadata.json` and `manifest.json`. The manifest records SHA-256 and byte size for every copied artifact.

Channel names are deliberately separate from store identifiers. Amazon ASIN, Kobo product ID, Apple Books ID and Google identifiers are recorded after publication; they never replace the ISBN in canonical metadata.

Google may additionally receive PDF when declared and supplied.
