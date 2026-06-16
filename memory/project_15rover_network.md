---
name: project-15rover-network
description: Classroom deployment has 15 rovers, 15 cameras, 15 laptops all on BaleNet simultaneously
metadata:
  type: project
---

15 rovers are deployed simultaneously on BaleNet (or the travel router equivalent). Each rover has its own ESP32 camera (192.168.50.x range) and a student laptop. The depth inference server runs on one shared Alienware desktop (RTX 5060 Ti) on the same network.

**Why:** Full STEM class size — not a single-rover dev setup.

**How to apply:** Keep queue sizes, port assumptions, and IP management in mind when making changes. The depth server queue is sized to 20 to handle classroom bursts. Average GPU load stays low because rovers only request depth when stopped (stop-and-stare pattern). Latency under full-class burst (~15 simultaneous requests) is ~300ms — acceptable for trapezoid control, worth flagging for any continuous PID depth use.
