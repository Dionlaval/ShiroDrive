# ShiroFOC weekend learning lab

**Start with [the interactive lab](index.html)**. Open `index.html` in a browser; it works offline, with no installation or server. Work through one chapter at a time alongside [the notebook](docs/NOTEBOOK.md).

This package turns the [learning plan](docs/PCB_DESIGN_LEARNING_PLAN.md) into worked models, experiments and board-specific explanations. It is designed for a mechanical engineer with a robotics and control background.

## Suggested route

| Session | Read and do | Approximate time |
|---|---|---|
| Saturday morning | Notebook §§1–3; lab “Switching”; exercises 1–3 | 1.5–2 h |
| Saturday afternoon | Notebook §§4–7; “Capacitors” and “Supply & energy”; exercises 4–8 | 2–3 h |
| Sunday morning | Notebook §§8–10; “Placement” and “Sensing”; exercises 9–12 | 2–3 h |
| Sunday afternoon | Notebook §11; decision record; write your own capacitor decision | 1–2 h |

Take breaks between models. You do not need to absorb all the equations before experimenting.

## Deliverables

- [Interactive lab](index.html): live switching, capacitor, RLC, gate-drive and sensing models. Hover/touch plots to inspect values; controls show units.
- [Guided notebook](docs/NOTEBOOK.md): physical explanations, worked numbers and predictions.
- [Board inputs](docs/BOARD_INPUTS.md): actual component values, operating targets and assumed parameters.
- [Model guide](docs/MODEL_GUIDE.md): derivations, topology definitions, implementation details and limits.
- [Exercises with answers](docs/EXERCISES.md): prediction-first experiments and numerical checks.
- [Decision record](docs/DECISION_RECORD.md): consequences for this board and what remains undecided.
- [Sources](docs/SOURCES.md): project evidence and primary engineering references.
- [Figures](figures/): standalone PNG and SVG plots, power-path diagram and actual placement overview.
- [Comparison CSV](data/comparison.csv), [JSON](data/comparison.json) and waveform CSVs: reusable numeric results.
- [Python model](models/build_models.py) and [browser model](models/lab_models.js): editable, documented implementations.
- [Runnable Jupyter notebook](ShiroFOC_learning.ipynb): optional computational companion; the browser lab requires no Python.
- [Validation notes](qa/VALIDATION.md): checks, coverage and known limitations.

## What is real, and what is an example?

The hardware snapshot is the **P1 schematic and P0 unrouted component placement**, as read on 19 September 2026. Component values come from the project. Motor parameters, cable impedance, capacitor parasitics and ceramic DC-bias retention are explicitly assumed. The ceramic candidates are study cases, not selected parts or released hardware changes.

The current schematic still has three 680 µF electrolytics. No schematic or PCB was changed by this learning package. Parts availability and fabricator validation were not performed, as requested earlier.

## Reproduce the calculations

With Python 3.10+ and the dependencies in [requirements.txt](models/requirements.txt):

```sh
python -m pip install -r learning/models/requirements.txt
python learning/models/build_models.py
python learning/models/build_package.py
python learning/models/validate_reference.py
node learning/models/check_models.cjs
node learning/models/check_lab_wiring.cjs
```

Run these commands from the repository root. The first Python script also works from another directory. The scripts write only learning artifacts, not hardware design files. The package includes the schematic analysis snapshot; regenerating that snapshot requires the KiCad skill's analyzer or an equivalent extraction.

The calculations use linear circuit models and ideal switches. They are useful for understanding and comparing choices; they do not constitute measured board performance, an EMC review, or a fabrication release.
