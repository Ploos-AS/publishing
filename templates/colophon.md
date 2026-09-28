<!--
Ploos Publishing colophon template.
Values in {{...}} are build-time substitutions.
Do not publish literal PENDING ISBN values in a release represented as ISBN-assigned.
-->

# {{title}}

{{#subtitle}}{{subtitle}}

{{/subtitle}}© {{year}} {{copyright_holder}}

Published by **Ploos AS**, Norway.

Edition: {{edition}}
Language: {{language}}

## ISBN

{{#isbn_epub}}- EPUB: {{isbn_epub}}
{{/isbn_epub}}{{#isbn_kindle}}- Kindle: {{isbn_kindle}}
{{/isbn_kindle}}{{#isbn_pdf}}- PDF: {{isbn_pdf}}
{{/isbn_pdf}}

{{#license}}License: {{license}}
{{/license}}
Source: {{source_repository}}

This publication was generated from common source material using the Ploos publishing workflow.
