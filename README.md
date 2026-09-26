# ShiroDrive

ShiroDrive is an independent motion-control project focused on modular motor-drive hardware and experimental robotic systems.

The current hardware direction includes both stepper control and compact, networked FOC servo modules.

This is an evolving engineering project.

---

## Core Direction

ShiroDrive currently explores:

- Custom stepper motor driver design
- Dynamic microstepping techniques
- Smooth motion across wide velocity ranges
- Resonance mitigation and control refinement
- CoreXY motion architectures

The stepper platform uses ESP32, while ShiroFOC is based on the STSPIN32G4 with its embedded STM32G431 motor-control MCU.

ESP32 provides:

- Real-time capable control
- Flexible peripheral configuration
- Wireless debugging and telemetry
- Rapid prototyping flexibility

STSPIN32G4 provides:

- Integrated STM32G4 real-time motor-control MCU
- Three external-MOSFET gate drivers
- Integrated current-sense op-amps and hardware protection comparators
- CAN-based modular communication
- Compact single-axis FOC architecture

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

### ShiroFOC

A single-axis, 48 V-class FOC servo module for robotics.

Planned features include:

- STSPIN32G4 controller and external three-phase MOSFET bridge
- Three-shunt phase-current sensing
- CAN communication to a coordinating motherboard
- Integrated magnetic encoder and 6-axis IMU
- External Hall and encoder inputs
- SWD programming and debug

See [ShiroFOC design constraints](ShiroFOC/docs/DESIGN_CONSTRAINTS.md) for the preliminary Rev A targets.

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
