# Publication catalog

`ploos-publish catalog` generates the normalized JSON feed intended to back a future `books.ploos.no` catalog.

By default only metadata with lifecycle status `published` is exposed. Draft, candidate, qualified and archived revisions are omitted from the public feed.

Example:

```sh
ploos-publish catalog books/*/publication.yaml -o dist/catalog.json
```

For preview/staging, `--include-unpublished` includes all lifecycle states.

Each language publication becomes a separate catalog entry and carries project/work identity, title, author, publisher, edition/revision, lifecycle and product ISBNs. Entries are sorted deterministically by title and language.

The feed is deliberately presentation-neutral. A static website, API, RSS/Atom adapter or other frontend can consume the same canonical JSON later.
