# ONIX for Books

Ploos Publishing can export a conservative ONIX 3.0 product record from canonical publication metadata.

```sh
ploos-publish onix publication.yaml --language nb --product epub -o dist/onix/nb-epub.xml
```

The exporter currently maps only canonical data that Ploos knows: product ISBN, title, language, author, publisher, edition number and publication year. It does not invent subjects, prices, descriptions, territories or other commercial metadata.

ONIX is product-oriented. Export therefore requires a language and product, and it refuses `PENDING` or missing ISBN values. Store-specific identifiers remain outside the ONIX ISBN identifier.

The initial implementation emits ONIX 3.0 reference-tag XML. Future M2/M3 qualification can add schema validation and richer commercial metadata when those fields become canonical.
