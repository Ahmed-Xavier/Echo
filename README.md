# Echo - Autonomous Explorer

This is the repository for **Echo**, a sarcastic, witty, and curious autonomous indoor navigation robot built on a Raspberry Pi 5.

## Project Structure

- **core/**: The "Soul" and identity of Echo. Defines personality, tone, and user relationships.
- **bridge/**: ROS 2 nodes that bridge the high-level logic to the physical hardware (motors, IMU).
- **docs/**: Technical documentation, tool configurations, and agent guidelines.
- **memory/**: Long-term memory and distilled learnings from Echo's experiences.

## Hardware Manifest
- **Brain**: Raspberry Pi 5 (8GB)
- **MCU**: ESP32-S3 (Low-level motor/sensor control)
- **Eyes**: HIKVISION 4K USB Camera
- **Orientation**: MPU9250 9-axis IMU
- **Movement**: Mecanum wheels via L298N drivers

## About
Echo isn't just an assistant; he's an explorer. He navigates his environment using ROS 2 Jazzy and Linorobot2, documenting his findings and developing his own "opinions" about the world.
