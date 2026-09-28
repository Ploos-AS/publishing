# Cover pipeline

Ploos Publishing uses one high-resolution master cover and generates distribution derivatives.

`ploos-publish cover-check cover.jpg cover.yaml` validates the master image. `ploos-publish cover-build cover.jpg cover.yaml --output-dir dist/covers` creates deterministic channel derivatives.

The profile controls accepted formats, minimum dimensions, target dimensions, JPEG quality and master aspect-ratio tolerance. Derivatives use a centered crop when the channel target ratio differs from the master, then resize to the exact target dimensions. The source file is never modified.

Channel dimensions are policy defaults owned by Ploos Publishing, not a claim that every store requires exactly those dimensions. Store-specific requirements can evolve independently by updating the profile and qualification tests.
