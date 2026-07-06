# 9-Channel Syringe Pump Hardware & Mechanics

## High-Level Intuitive Explanation
This entry locks down the mechanical hardware for the 9-channel syringe pump. The core challenge was balancing speed, torque, and cost using cheap 28BYJ-48 stepper motors. 

Initially, an M4 threaded rod was proposed, but the math showed it would take over 7 minutes to pull a 20mL vacuum because the motor has a 1:64 internal gear reduction. We looked at 3D printing high-pitch screws (too weak), rack and pinion (too bulky for 9 parallel channels), and a pulley/string winch (risk of insufficient torque). The final winner is the **T8x8 lead screw**. It fits the budget, moves 8mm per rotation (11x faster than M4), and retains enough leverage so the weak steppers don't stall. 

To keep the physical footprint short and low cost, we used industrial 20cc syringes. For the motor-to-screw connection, we bypassed expensive aluminum couplers by 3D printing a custom resin coupler. It uses a "captive nut" design where a real metal nut handles the clamping force, saving the brittle resin from snapping.

Finally, for the pneumatic plumbing, we are using dirt-cheap Mineshima 0.6mm OD hobby needles pushed directly into 0.5mm ID silicone tubing. To prevent the tiny 0.37mm hole from acting like a massive restrictor valve, the needles are cut down to just 3mm long. Standard cutters crush the pipe, so they are cut with a blade and then clamped back into a perfect circle to ensure unrestricted airflow.

## Implementation Plan
1. **CAD & Print Couplers:** Model the custom 5mm D-shaft to 8mm lead screw coupler. Ensure the hex pocket is sized slightly larger (e.g., +0.2mm) to accommodate resin shrinkage for the captive nut. Print 9 units in tough/ABS-like resin.
2. **Hardware Assembly:** Mount the 9 uxcell 50cc syringes parallel to each other. Attach the T8x8 lead screws and the printed couplers to the 28BYJ-48 motors. 
3. **Plumbing:** Cut 9 Mineshima needles to 3mm. Use a clamp/pliers to gently massage the cut ends back to a perfect circular cross-section. Push them into the 0.5mm ID silicone tubes.
4. **Wiring & Code:** Wire the 9 ULN2003 drivers to the Arduino Mega 2560 (using pins 22-53 and 2-5). Flash the non-blocking "Watchdog" serial control code to test simultaneous high-speed movement without overheating the idle motors.