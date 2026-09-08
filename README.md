# Three Image Transition

An interactive WebGL experiment that breaks two photographs into animated triangles and transitions between them along cubic Bézier paths.

[View the demo](https://tino-three.netlify.app/)

## Interaction

- Drag horizontally to scrub the animation.
- Press <kbd>P</kbd> to pause or resume.
- The animation resolves to a still image when the operating system requests reduced motion.

## Implementation

This is a dependency-free static deployment. It uses Three.js, Buffer Animation System (BAS), and GSAP from pinned CDN URLs. The experiment intentionally remains on Three.js r75 because its geometry implementation relies on APIs removed from modern Three.js releases.

Serve the directory over HTTP rather than opening `index.html` directly:

```bash
python3 -m http.server 8080
```

Then visit <http://localhost:8080>.

## Maintenance status

This is a preserved creative-coding demo, not a template for a new WebGL application. A ground-up modernization would replace the legacy geometry pipeline and GSAP API rather than incrementally upgrading them.

## Licence

The project code is MIT licensed. Photograph rights remain with their respective owner.
