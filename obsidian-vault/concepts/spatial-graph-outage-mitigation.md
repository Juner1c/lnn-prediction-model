---
title: Spatial Graph Outage Mitigation
category: concept
tags: [gnn, spatial-graph, outage-mitigation, haversine, imputation]
created: 2026-07-23T09:50:00Z
updated: 2026-07-23T09:50:00Z
---

# Spatial Graph Outage Mitigation

Spatial Graph Outage Mitigation is a neural network architecture pattern used in multi-station IoT/weather sensor networks to handle missing readings, sensor failures, and offline down stations.

## Architecture & Equations

1. **Haversine Distance Adjacency Matrix**:
   Constructs a normalized spatial graph matrix $A_{\text{norm}}$ from GPS coordinates ($\text{lat}_i, \text{lon}_i$):
   $$d_{ij} = 2 R \cdot \arcsin\left(\sqrt{\sin^2\left(\frac{\Delta \phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta \lambda}{2}\right)}\right)$$
   $$A_{ij} = \exp\left(-\frac{d_{ij}^2}{\sigma^2}\right)$$

2. **Node Outage Masking & Message Passing**:
   When station node $i$ goes offline or emits unphysical misreadings ($T \le 5^\circ\text{C}$), a boolean mask matrix $M \in \{0, 1\}^{B \times N \times S}$ zeroes out corrupted signals. Spatial graph convolutions aggregate feature embeddings from active neighboring nodes:
   $$H^{(l+1)} = \sigma\left(D^{-\frac{1}{2}} A D^{-\frac{1}{2}} H^{(l)} W^{(l)}\right)$$

3. **Empirical Results**:
   In testing over 12 Bataan weather stations with 20% station dropouts (e.g. *Limay* or *Quinawan* down), spatial message passing maintains Temperature forecast precision at **`3.2219 °C` RMSE** without throwing `NaN` or failing.
