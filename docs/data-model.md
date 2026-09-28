# Publishing data model

Ploos Publishing separates intellectual works, editions, publications, products and distribution.

```text
Project -> Work -> Edition -> Publication -> Product -> Distribution
```

- **Project**: source/repository identity, e.g. EduNumbers.
- **Work**: the intellectual work independent of language or file format.
- **Edition**: a materially defined edition of the work.
- **Publication**: a language-specific publication of an edition.
- **Product**: a format-specific product, e.g. EPUB or PDF. ISBN belongs here.
- **Distribution**: placement of a product in Amazon KDP, Kobo, Apple Books, Google Play Books, or another channel.

A store identifier is not an ISBN. Git/software versions are not book editions.
