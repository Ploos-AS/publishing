# Store metadata export

Store metadata is derived from canonical publication metadata; it is not maintained as a second source of truth.

Example:

```sh
ploos-publish store-metadata publication.yaml --channel amazon --language nb -o dist/metadata/amazon-nb.json
```

Supported channel names are `amazon`, `kobo`, `apple`, and `google`.

The export includes project/work identity, language, localized title, canonical author/publisher/copyright/license, edition and revision, selected product, its ISBN status, and the store's external identifier.

ISBN and store identifiers remain separate. An Amazon ASIN, Kobo product ID, Apple Books ID, or Google identifier must never be substituted for an ISBN.

The JSON export is an internal normalized interchange artifact. It can later feed channel-specific upload/API adapters without forcing store-specific fields into the core publication model.
