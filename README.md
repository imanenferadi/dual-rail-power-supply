# Adjustable Dual-Rail Power Supply (±13V) + Arduino Oscilloscope

A linear, adjustable ±13V dual-rail DC bench power supply, designed and built for
Sharif University of Technology's Circuits Lab I (Dr. Alavi). Every stage — rectifier,
filter, and regulator — was validated three ways: hand calculation, LTspice simulation,
and real hardware measurement.

This was built at home, where I didn't have access to lab equipment like an
oscilloscope. So I built one myself first — a second, self-contained project:
a **two-channel Arduino-based oscilloscope** with a live matplotlib GUI, used
throughout to capture and verify every waveform in the power supply.

## Power supply

| | |
|---|---|
| Topology | Center-tapped transformer → full-bridge rectifier → capacitive filter → LM317 / LM337 adjustable regulators |
| Output | 0 to ±13V, adjustable via a dual (1kΩ + 100Ω series) potentiometer |
| Rectifier diodes | 1N5822 Schottky (low forward drop, fast recovery) |
| Filter capacitors | 2200µF per rail, sized for <100Hz ripple with a 10Ω / 1.5A load assumption |
| Protection | Input/output diodes on each regulator (reverse-current, discharge, reverse-battery protection), ADJ-pin bypass capacitor for ripple rejection, output capacitor for transient response, discharge resistor across the filter caps |
| Enclosure | Custom metal case with fuse, IEC inlet, power switch, and a digital V/A display |

Full design derivation (bridge sizing, filter capacitor sizing, LM317/LM337 resistor
network, protection diode reasoning) is in [`power-supply/`](power-supply).

**Verified output:** ~12.7V measured on a Victor VC97 multimeter, matching the
built-in digital display and the LTspice sweep within a few tens of millivolts.

### Photos

| | |
|---|---|
| ![Final unit](power-supply/photos/final-unit-front.jpg) | ![Display](power-supply/photos/final-unit-display.jpg) |
| ![Internal wiring](power-supply/photos/internal-wiring.jpg) | ![Multimeter verification](power-supply/photos/multimeter-verification.jpg) |

### Schematic & simulation

![Schematic](power-supply/schematics/schematic.png)

LTspice parametric sweep of the adjustment resistor, showing the regulated output
settling across its full adjustable range:

![Output voltage sweep](power-supply/simulation/output-voltage-sweep.png)

## Arduino oscilloscope

To measure and verify waveforms without lab equipment at home, I built a
two-channel "oscilloscope" from an Arduino and a Python visualizer:

- A resistor-divider + level-shifting front end (derived analytically, not just
  guessed) scales the transformer's ±20V swing down into the Arduino's safe
  0–5V ADC window, centered at 2.5V.
- [`ArduinoCode.ino`](arduino-oscilloscope/firmware/ArduinoCode.ino) streams both
  ADC channels over serial at 115200 baud.
- [`oscilloscope.py`](arduino-oscilloscope/visualizer/oscilloscope.py) is a live
  two-channel viewer built on matplotlib: per-channel Vpp/Vmax/Vmin/Vrms readouts,
  channel show/hide toggles, and pause/resume on the spacebar.

Measured ADC resolution: **~26.4mV**, accurate enough to validate every stage of
the power supply against its LTspice prediction.

### Photos

| | |
|---|---|
| ![Level shifter board](arduino-oscilloscope/photos/level-shifter-board.jpg) | ![Live two-channel capture](arduino-oscilloscope/photos/live-two-channel-capture.jpg) |

The live capture above shows two channels of the transformer's secondary windings —
180° out of phase, as expected from the center tap — captured and measured entirely
through the home-built scope.

## Course context

Built as the term project for **Circuits Lab I**, Sharif University of Technology,
Spring 2026 (Dr. Alavi). The full lab report — in Persian, with the theory,
simulation, and practical measurement for every block — is at
[`report/lab-report-fa.pdf`](report/lab-report-fa.pdf).
