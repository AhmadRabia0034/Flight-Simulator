# Distributed HIL 6-DOF Flight Simulator

## ✈️ Overview
This repository contains the complete source code and configuration files for a distributed Hardware-in-the-Loop (HIL) flight simulator. The project integrates a virtual flight environment (FlightGear) with a physical 6 Degrees-of-Freedom (6-DOF) Stewart platform to provide real-time, highly synchronized motion feedback.

## ⚙️ System Architecture
The architecture is fully distributed to ensure low latency and high fidelity:
* **FlightGear Engine:** Acts as the primary flight dynamics generator.
* **Raspberry Pi (Middleware):** Handles Python-based Inverse Kinematics (IK) calculations and decodes UDP telemetry streams.
* **Arduino Mega:** Parses physical cockpit inputs from the custom-built dashboard and flight yoke.
* **Arduino Uno:** Drives the 6-DOF Stewart platform servos based on the computed IK angles.

## 📂 Repository Structure
* `/Python_IK/`: Contains the Python scripts running on the Raspberry Pi for UDP packet decoding and Inverse Kinematics math.
* `/Arduino_Firmware/`: Contains the C++ firmware for both the Arduino Uno (Actuator Control) and Arduino Mega (Cockpit Interfaces).
* `/Network_Config/`: Includes the custom XML protocol files required by FlightGear to structure and output the telemetry data properly.

## 🚀 Key Features
* **Real-Time Motion:** Sub-50ms visual-vestibular latency.
* **Closed-Loop Verification:** IMU integration for physical telemetry tracking.
* **Distributed Computing:** Prevents CPU bottlenecking by offloading math to the Raspberry Pi.

## 📝 License
This project is licensed under the MIT License.
