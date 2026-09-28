# Naming policy

A repository/project name does not have to be the publication title.

For Edu projects, use the stable project identity for source code, automation and repository naming, while giving each publication a clear reader-facing title in its language.

Example:

- Project/repository: `EduNumbers`
- Norwegian book title: **Tallsystemer**
- English book title: **Number Systems**

Translations are separate language editions and may use natural titles rather than literal branding. `EduNumbers` remains the project identifier in metadata.

Recommended metadata fields:

```yaml
project: EduNumbers
titles:
  nb: Tallsystemer
  en: Number Systems
```

A subtitle may be added independently per language. ISBNs identify publication products/editions; they do not require the Git repository and book to share a title.
