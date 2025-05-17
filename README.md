Project 2: Unslotted CSMA-CA vs TSCH Orchestra

This project explores and compares two MAC protocols used in low-power wireless networks: Unslotted CSMA-CA and TSCH (Time Slotted Channel Hopping) using the Orchestra scheduler.

The goal is to understand how these protocols behave under various network conditions and disturbances, and how they impact performance in terms of throughput, latency, and robustness.

Objectives

Minimum Requirements:
- Throughput Measurement  
  Determine the breaking point (maximum capacity before performance degradation) for both schedulers.

- Latency Measurement  
  Measure the latency introduced by Unslotted CSMA-CA and TSCH Orchestra.

- Behavior Under Disturbances  
  Analyze how each protocol reacts to external disturbances (e.g., interference, packet loss).

- Exponential Backoff Analysis  
  Explain the concept of exponential backoff and its effect on network performance.

Extra (Optional):
- Slotframe Size Impact  
  Investigate how different slotframe sizes affect TSCH performance.

- Multi-Channel vs Single-Channel  
  Provide an in-depth comparison of:
  - TSCH’s multi-channel approach
  - Unslotted CSMA-CA’s single-channel usage  
  Discuss how this influences throughput, reliability, and latency.

Technologies
- Contiki-NG
- TSCH + Orchestra
- CSMA-CA
- IEEE 802.15.4

Metrics to Track
- Packet delivery ratio (PDR)
- Average end-to-end delay
- Number of retransmissions
- Channel utilization

------------------------------



