# Validation and limitations

## Completed

- Read the native schematic with the KiCad analyzer; manually checked key values and connections against the P1 netlist, particularly sense nodes and DNP feedback capacitors.
- Checked the half-bridge periodic mean current against its specified operating point.
- Checked three-phase current summation and analytical mean input current.
- Checked capacitor charge balance and Kirchhoff current balance in the periodic network model.
- Recomputed representative three-phase cases at twice the time resolution; see [numerical_checks.json](numerical_checks.json) for actual differences.
- Compared the browser's exact 2×2 transient solution against independent SciPy state-space results for underdamped, overdamped and critically damped cases. See [javascript_checks.json](javascript_checks.json).
- Swept extreme transient control values for finite outputs and checked passive impedances remain finite and positive.
- Checked HTML IDs, referenced controls, links and local artifact paths; see [artifact_checks.json](artifact_checks.json).
- Exercised all seven navigation handlers and 85 control updates using DOM/canvas stubs, including minimum/maximum values. All plotted coordinates and result text remained finite. This checks script wiring, not actual browser layout; see [lab_wiring_checks.json](lab_wiring_checks.json).
- Inspected the standalone exported figures visually. These use the same physical models described in the model guide.

## Explicit gaps

**Interactive browser rendering was not visually verified.** Automatic navigation to the local HTML file was rejected by the browser's local-file security policy. No alternate browser route was used to bypass that block. The code, references and numerical functions were checked directly. Open `index.html` locally to use the delivered lab.

**No successful SPICE verification is claimed.** A skill-driven LTspice batch attempt detected the installed application, but its calls failed without useful simulator output; all twenty attempted automatic cases were skipped. The raw attempt is retained in [spice_attempt.json](../data/spice_attempt.json). Some automatic divider detections also do not represent the complete relevant circuit. None was treated as evidence against the board. The curated numerical models and manually checked topology are the teaching basis.

**This is not a full design review.** No fabricated board measurements, switching-device nonlinear model, routed parasitic extraction, EMC test, thermal qualification, parts-availability validation or fabricator validation was performed. The physical assumptions dominate uncertainty even where numerical agreement is excellent.

## Reproduce

From the repository root, after installing the model requirements:

```sh
python learning/models/build_models.py
python learning/models/build_package.py
python learning/models/validate_reference.py
node learning/models/check_models.cjs
node learning/models/check_lab_wiring.cjs
node --check learning/lab.js
```

`ShiroFOC_learning.ipynb` contains runnable code cells, with no fabricated execution outputs. The underlying model functions were executed by the scripts above. Optional notebook display imports require a Jupyter environment; the offline HTML lab does not.
