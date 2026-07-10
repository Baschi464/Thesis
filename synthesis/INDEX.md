# Thesis Synthesis Manifest

This file tracks all captured engineering decisions, experimental data, and theoretical breakthroughs chronologically.

| Date | Type | Description | File Links |
| :--- | :--- | :--- | :--- |
-  2026-07-06 | Design Decision | 9-Channel Syringe Pump Actuation and Hardware Sourcing | [LaTeX](2026-07-06_syringe_pump_hardware.tex), [Markdown](2026-07-06_syringe_pump_hardware.md) |

- 2026-07-06 | implementation | Firmware, Python communication, GUI, and manual control | 2026-07-06_firmware-python-arduino-gui-manual-control.tex, 2026-07-06_firmware-python-arduino-gui-manual-control.md

- 2026-07-06 | design decision + numeric data | Lizard robot system architecture, global specs (5.8 g, 85 mm, 4 legs) and operating regime | 2026-07-06_lizard-robot-architecture.tex / .md
- 2026-07-06 | design decision + numeric data | Coupled body–tail three-chamber segment: geometry (6 mm OD, 26/33 mm, 0.4 mm wall), circumferential loops 1.5 mm, central axial fiber, body/tail naming convention | 2026-07-06_coupled-bodytail-actuator-design.tex / .md
- 2026-07-06 | design decision + theoretical idea | Central connector: crossed/uncrossed <1 mm channel routing selects S vs U mode; inlet asymmetry; P_t = αP_b abstraction (unverified mechanism, flagged) | 2026-07-06_pneumatic-coupling-connector.tex / .md
- 2026-07-06 | design decision + numeric data | Leg actuators: single-chamber, 24/30 mm, double-helical fiber ~25°, longitudinal constraint fiber, 90° @ 13 kPa; suction cups 10 mm OD / 3 mm vacuum height, actively evacuated | 2026-07-06_leg-actuator-suction-foot.tex / .md
- 2026-07-06 | numeric data + design decision | Materials: EcoFlex 00-30 (bodies) vs Elastosil M4601 (caps/feet, datasheet table); cure 90 °C 90/60 min; KE44-T bond 90 °C 90 min | 2026-07-06_materials-and-bonding.tex / .md
- 2026-07-06 | design decision (process) | Fabrication: brass 120° fan-core mold with 0.5 mm acrylic spacers; ethanol capillary demolding; hand fiber wrapping | 2026-07-06_fabrication-molding-process.tex / .md
- 2026-07-06 | experimental result | Miniaturized segment characterization: 3x vs 1x (182° @ 14.8 kPa vs 173° @ 16.4 kPa); central fiber effect (180° @ 15.0 kPa vs 173° @ 16.4 kPa) | 2026-07-06_bending-characterization-miniaturized.tex / .md
- 2026-07-06 | experimental result + modeling constraints | Vertical U-bend load tests (10.5 / 10.9 / 11.4 kPa for 0 / 2.0 / 5.7 g tip loads); wall-transition constraints: gravity, posterior-hinge, ChArUco gravity direction | 2026-07-06_vertical-ubend-loads-wall-transition.tex / .md
- 2026-07-11 | design decision + theoretical idea | AI-controller forward-model architecture: per-actuator Gaussian Process on Δz (prior+residual vs. model-free variants), Matérn-5/2+ARD kernel chosen over RBF for the reversal-deadzone scarp, uncertainty used to flag free-space→loaded-gait coverage gaps; geologist/probe metaphor; figure is a synthetic-data placeholder pending real single-actuator recordings; includes related decisions on composition, controller, hysteresis protocol, and augmentation policy | 2026-07-11_gp-forward-model.tex / .md