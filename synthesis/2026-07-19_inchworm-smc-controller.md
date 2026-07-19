# Inchworm pneumatics — sliding mode controller

The pneumatic hardware can only do three crude things per channel: open the
in-valve, open the out-valve, or hold. Air is springy and non-linear, and
pushing (pump on) is much stronger than passively bleeding air out — so the
system is lopsided and hard to tune with a plain PID. The controller's job is
to hit a target pressure smoothly and hold it, using only these on/off valves,
without buzzing them to death.

**Sliding mode, in plain terms.** Instead of controlling pressure directly,
SMC watches a single combined quantity `s = λ1·(error) + λ2·(rate of error)`.
When `s = 0`, both the error and how fast it's changing are under control, so
the pressure glides onto the target instead of overshooting. λ1 sets how
aggressively it chases the target; λ2 adds damping so it doesn't ring.

**Killing the chatter.** Textbook SMC slams the control fully positive or
fully negative depending on which side of `s=0` you're on — which for on/off
valves means rapid open/close chatter that wears the solenoids out. The fix is
a **boundary layer**: near the target (`|s| ≤ Φ`) the effort is softened with a
saturation function so `u` ramps between −1 and +1 instead of snapping. Φ is
the width of that "be gentle now" zone.

**From effort to valve pulses.** The valves can't be "35% open," so the
effort `u` becomes a pulse width: `t_pulse = |u|·K_gain`. Sign of `u` picks
direction (+ = inflate, − = deflate).

**The energy-saving trick (asymmetric deflation).** Deflating doesn't always
need the vacuum pump. If only a little deflation is needed (`|u| < 0.4`) and
the chamber is still above atmospheric, the controller just cracks the exhaust
valve and lets the air bleed out on its own — pump off, free energy. Because
that bleed gets weaker as pressure drops, the pulse is stretched inversely
with pressure to keep the rate steady. Only for big deflation or actual
sub-atmospheric vacuum does it fire the vacuum pump.

**Pump manager.** All 8 channels think independently, but the two pumps are
shared. A supervisor turns a shared pump on only if some channel is actually
asking for a real pulse (`t_pulse > 30 ms`), so the pumps aren't running for
trivial nudges.

The step-response figure is the proof it works: fast rise, no sustained
chatter, holds the target.

## Implementation

No further implementation needed — the controller is implemented and its step
response is the delivered result. Figure already staged:
`figures/stepresponse.eps`. Note for later: the tuning constants (λ1, λ2, Φ,
K_gain) are referenced symbolically; if the thesis should report their numeric
values, pull them from the Arduino firmware and add them to the text.
