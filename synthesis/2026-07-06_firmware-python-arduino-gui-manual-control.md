# Firmware, communication, GUI, and manual control

The system is really one loop split across two runtimes. The Arduino firmware is the motion executor: it receives a framed command, updates the stepper targets, moves the nine syringe channels, and keeps sending back actual positions so the operator can see what the hardware is doing. The Python application is the supervisory layer: it opens the serial port, formats the same protocol that the firmware expects, and turns user actions in the GUI into motion commands.

The manual workflow matters because it defines how the operator thinks about the machine. A channel can be jogged in small increments, then marked as a home reference, then captured as a preferred start pose. Those references are saved locally, so the GUI does not forget them after a restart. Live Control is intentionally conservative: it pauses when the user leaves the tab, and the firmware watchdog holds position if communication stops. That makes the interface feel less like a raw command sender and more like a controlled operating panel.

## Implementation

No further implementation is needed for this synthesis entry itself. The text captures the current behavior of the firmware, the Python serial layer, the tabbed GUI, and the manual home/start workflow. If this needs to be inserted into the thesis source or expanded with a figure later, that can be done in a follow-up pass.