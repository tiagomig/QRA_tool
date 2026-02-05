<!-- Copilot instructions for the QRA_tool repository -->

# QRA_tool — AI coding assistant guidance

This file gives focused, actionable context to an AI editing this repository so you can be productive quickly.

1) Big-picture architecture
- Frontend: plain HTML + ES modules under `src/` (key files: `src/visualize.js`, `src/objects.js`, `src/helpers.js`, `src/workers.js`). The built bundle is `bundle.js` (output of `webpack.config.js`) and is loaded as a module from `index.html`.
- Data: GeoJSON tiles live in `data/`. Processed population tiles contain properties used by the frontend: `B` (population), `T` (GA time fraction), `v` (GA mean speed), and optional `Dn` (drone density / 1st-party risk).
- Backend / processing: Python scripts (`data_processing.py`, `risk_calculations.py`, `data_cleaning.py`) compute `T`, `v`, `p` and write GeoJSON files consumed by the frontend.

2) Why things are structured this way
- Heavy spatial computation is split: browser performs route buffering, unions and uses Web Workers (`src/workers.js`) to parallelize tile processing. Pre-processing (Python) enriches GeoJSON with traffic statistics so the browser can remain interactive.
- Many spatial libraries are loaded from CDN in `index.html` (Leaflet, Turf, polyclip-ts, RBush, noUiSlider). The code expects these globals (e.g. `turf`, `RBush`, `polyclip`) to be present at runtime.

3) Important files / references (start here)
- UI & control flow: `src/visualize.js` (Visualization class — main entry for user interactions).
- Geometry helpers & R-Tree: `src/helpers.js` (styling, `createRTree()`, `treeBboxIntersect()` — uses `RBush` global).
- Worker logic: `src/workers.js` (uses `importScripts` to load Turf; receives feature subsets and returns per-edge aggregates).
- Data processing: `data_processing.py` and `risk_calculations.py` (Python-side computation that populates `data/*.geojson`).
- Static page: `index.html` (shows which libraries are included via CDN and how `bundle.js` is loaded).

4) Build / run / test workflows (practical commands)
- Rebuild frontend bundle (produces `bundle.js` consumed by `index.html`):
  - Install dev deps: `npm install`
  - Bundle: `npx webpack` (or `npx webpack --mode production`). Webpack entry is `script.js` and output is `bundle.js` in repo root.
- Serve the site locally (Workers and XHR/fetch require an HTTP server; opening `index.html` via file:// will fail):
  - Quick option: `npx http-server . -c-1 -p 8080` or `python -m http.server 8080` and open `http://localhost:8080`.
- Frontend tests: there's no automated browser test harness configured. `tests/*.js` are small browser-run scripts (swap the script in `index.html` to run). `package.json` contains `"test": "jest --coverage ./tests"` but `jest` is not listed in `devDependencies` — running `npm test` will fail unless `jest` is installed.
- Python data pre-processing: run `python data_processing.py` (ensure dependencies installed). Key Python dependencies inferred from imports: `traffic` (traffic.core), `shapely`, `scipy`, `tqdm`.

5) Project-specific conventions & gotchas
- Global libraries: runtime expects Turf (`turf`), RBush (`RBush` global), polyclip (`polyclip` global), Leaflet, and noUiSlider to be included via CDN in `index.html` — do not remove those script tags unless you provide equivalent bundling.
- Worker path: `src/workers.js` is spawned directly from the browser (`new Worker('./src/workers.js')`) and uses `importScripts`. When switching to bundlers that transform worker code, ensure the worker remains reachable at that path or adopt a bundler plugin that emits a separate worker file.
- R-Tree usage: `helpers.createRTree()` expects features with polygon coordinates laid out like the GeoJSON files in `data/` (see `data/*.geojson`). Keep the same feature `properties` keys (`B`, `T`, `v`, `Dn`).
- Tests are semi-manual: `tests/testing_rtree.js` imports `src/visualize.js` and is intended to be loaded in the browser for visual/manual verification.

6) Quick examples to reference in edits
- When changing feature property names, update both the Python pre-processing outputs (`data_processing.py`) and consumer code in `src/helpers.js` and `src/workers.js` — they directly access `feature.properties.B`, `T`, `v`, `Dn`.
- When adding a new global lib, update `index.html` (CDN tags) and confirm `bundle.js` or `src/*.js` do not try to re-import the same library as an ES module.

7) Contribution rules for AI edits
- Preserve existing runtime globals loaded in `index.html` or explicitly migrate them (do not silently remove CDN inclusions).
- Keep `bundle.js` as the artifact produced by `webpack`. If modifying module imports, ensure `npx webpack` still builds without errors.
- Avoid breaking the worker contract: worker receives `[subset, groundBuffers, airBuffers, circles, tileArea]` and returns `[edgesIntersectedPopulations, circlesPopulations, edgesTimes, edgesAverageSpeeds, edgesMaxPopulations, edgesDroneDensities]`.

If any of this is unclear or you'd like me to expand any section (examples of typical edits, a sample `requirements.txt`, or a script to run the app locally), tell me what to add and I will iterate.
