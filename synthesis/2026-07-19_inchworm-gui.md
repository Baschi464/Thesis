# Inchworm pneumatics — graphical user interface

This is the operator's cockpit for the 8-channel pneumatic box. It was
commented out of the conference paper for space and is reinstated here. It's a
custom app that talks to the Arduino over serial in real time, both ways
(sends targets, reads back live pressures). It splits cleanly into two jobs:
**design a motion** and **run a motion**.

**Program tab — author an "action".** An "action" is one coordinated move of
the whole robot: a target-pressure-vs-time curve for every channel, all
running together. You don't draw the curve freehand — you drop a few `(time,
pressure)` keypoints and the app interpolates between them. So "ramp channel 1
to 15 kPa over 2 s, hold, then vent" becomes three keypoints. This is how the
bending/elongation timing of a gait phase gets dialed in precisely.

**Live Control tab — run and watch.** Finished actions are saved as **JSON**
files in a shared library, so they persist and can be recombined. From here
you fire sequences of actions to actually drive the robot, and the tab plots
**target vs. measured pressure live** for every channel — instant feedback on
whether the SMC is tracking. You can export up to 60 s of that plot history,
which is where the step-response and gait-tracking data for analysis come
from.

The design philosophy: separate *composing* a motion (slow, careful,
keypoint editing) from *executing* it (fast, live, monitored), so gait
development is repeatable rather than ad-hoc.

Note: this is the interface for the **solenoid** pneumatic system of the
inchworm robot. It is a different piece of software from the manual
syringe-pump jog/home interface documented for the lizard robot — don't
conflate them.

## Implementation

No further implementation needed — the GUI exists and is in use. Figures
already staged: `figures/programTab.eps`, `figures/controltab.eps`. If the
thesis should document the serial protocol or the JSON action schema in
detail, that would be a separate follow-up entry pulling from the GUI source.
