# Adjustable Dual-Rail Power Supply (±13V) + Arduino Oscilloscope

This is an adjustable ±13V power supply with a positive and negative rail, built for my Circuits Lab I course at Sharif University of Technology. For every stage of it — the rectifier, the filter, the regulator — I first did the math by hand, then checked it in LTspice, then checked it again on the actual hardware.

I built the whole thing at home, and the one piece of equipment I didn't have was an oscilloscope. So before I could really test anything, I ended up building one out of an Arduino and some Python, and used that for basically every waveform in this project. More on that below.

## The power supply

It's a fairly standard linear supply: a center-tapped transformer feeding a full-bridge rectifier (1N5822 Schottky diodes, mostly because of their low forward drop), big 2200µF filter caps on each rail, and then an LM317/LM337 pair doing the actual regulation. Output goes from 0 to about ±13V, set with two potentiometers in series (1kΩ + 100Ω) so I could get fine adjustment without needing an expensive multi-turn pot.

There's a bit of protection built in too — diodes across each regulator to stop it from getting fried if the output caps discharge backwards or someone hooks up a battery, a bypass cap on the ADJ pin to keep ripple out of the feedback, and a bleeder resistor so the filter caps don't stay charged after you switch it off.

Everything's in a metal enclosure with a fuse, an IEC power inlet, a switch, and a small digital V/A display on the front. I checked the final output with my own multimeter and got about 12.7V, which lined up with both the display and what LTspice predicted, so I was pretty happy with that.

The full derivation — how I sized the bridge, the filter caps, the LM317/LM337 resistors, why the protection diodes are there — is written up in [`power-supply/`](power-supply).

### Photos

| | |
|---|---|
| ![Final unit](power-supply/photos/final-unit-front.jpg) | ![Display](power-supply/photos/final-unit-display.jpg) |
| ![Internal wiring](power-supply/photos/internal-wiring.jpg) | ![Multimeter verification](power-supply/photos/multimeter-verification.jpg) |

### Schematic & simulation

![Schematic](power-supply/schematics/schematic.png)

Here's an LTspice sweep of the adjustment resistor, showing where the output settles across its full range:

![Output voltage sweep](power-supply/simulation/output-voltage-sweep.png)

## The Arduino oscilloscope

Since I didn't have a real scope at home, I needed some way to actually look at the waveforms instead of just trusting the math. The idea was simple enough: read the signal with an Arduino's ADC and plot it on a laptop.

The tricky part is that the Arduino can only read 0–5V, and the transformer swings up to about ±20V, so I had to build a small resistor-divider and level-shifting circuit to squeeze that down into a safe range centered around 2.5V. I worked the resistor values out by hand (superposition, mostly) rather than just guessing and checking.

- [`ArduinoCode.ino`](arduino-oscilloscope/firmware/ArduinoCode.ino) just reads both analog pins and streams them over serial.
- [`oscilloscope.py`](arduino-oscilloscope/visualizer/oscilloscope.py) reads that serial data and plots it live with matplotlib — shows Vpp/Vmax/Vmin/Vrms for each channel, lets you toggle channels on and off, and you can pause the plot by hitting spacebar.

Worked out to about 26mV of resolution, which turned out to be good enough to actually verify every stage of the power supply against the simulations.

### Photos

| | |
|---|---|
| ![Level shifter board](arduino-oscilloscope/photos/level-shifter-board.jpg) | ![Live two-channel capture](arduino-oscilloscope/photos/live-two-channel-capture.jpg) |

That second photo is a live capture from the scope — two channels of the transformer's secondary, 180° out of phase like you'd expect from a center tap. Good sanity check that the whole thing actually worked.

## The full report

This was originally a term project for Circuits Lab I at Sharif University of Technology (spring 2026, Dr. Alavi). The full lab report is in Persian and goes through the theory, simulation, and practical results for every block — it's at [`report/lab-report-fa.pdf`](report/lab-report-fa.pdf) if you want the details.
