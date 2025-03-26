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

Extra inf Andreas:

Throughput.  Pakketten per secondesteeds verhogen en dan PDR(Packet delivery ratio) meten, deze zal plotseling PDR dalen.


Max BB is 200kbits per seconden
elk pakket maximaal 127 bytes


Disturbances zijn speciale nodes in cooja
Exponantial Backoff (Slimme wachttijd strategie) ... is setting in cooja.  Nakijken wat maximaal is en invloed op trouchput en latency

We behouden de setup (aantal nodes en posities), we kiezen de topologie en blijft behouden

Bonus :  Als slotframe van 7 naar bv 9 gaat


Vandaag : setup netwerk
Disturbance node
idee exponantial backoff






