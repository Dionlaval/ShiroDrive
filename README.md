# ShiroDrive

ShiroDrive is an independent motion control project focused on building modular stepper motor control hardware and applying it to experimental robotic systems.

The current focus is precise, high-quality motion using custom electronics and firmware — starting with stepper control and CoreXY machines.

This is an evolving engineering project.

---

## Core Direction

ShiroDrive currently explores:

- Custom stepper motor driver design
- Dynamic microstepping techniques
- Smooth motion across wide velocity ranges
- Resonance mitigation and control refinement
- CoreXY motion architectures

All control and firmware development is currently based on the **ESP32** platform.

ESP32 provides:

- Real-time capable control
- Flexible peripheral configuration
- Wireless debugging and telemetry
- Rapid prototyping flexibility

---

## Building Block

### ShiroDrive Step

A custom stepper motor control platform.

Focus areas:

- Dynamic microstepping
- High-speed stability
- Clean current control
- Modular PCB design
- Firmware-driven motion refinement

This board forms the foundation of all current machines.

---

## Experimental Machine

### Manga Draw

A CoreXY-based pen plotting platform.

Purpose:

- Investigate high-speed planar motion
- Develop scalable XY architecture
- Render anime-style posters and manga panels with precision
- Serve as a validation platform for ShiroDrive Step

The architecture is designed to scale beyond desktop format.

---

## Development Status

### Currently Working On

- ShiroDrive Step PCB iteration
- Motion firmware development (ESP32)
- CoreXY Manga Draw platform integration

### Next Steps

- Refinement of dynamic microstepping
- Mechanical rigidity improvements
- Higher current driver revisions
- Closed-loop motion experimentation

---

ShiroDrive documents the process of building motion systems from first principles — hardware, firmware, and mechanical integration.