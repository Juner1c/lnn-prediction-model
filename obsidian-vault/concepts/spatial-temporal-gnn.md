---
title: Spatial-Temporal Graph Neural Networks (STGNN)
category: concept
tags: [gnn, stgcn, graphsage, gat, spatial-temporal, weather-forecasting]
sources: [arXiv STGNN Surveys, PyTorch Geometric Docs]
created: 2026-07-20T11:38:00Z
updated: 2026-07-20T11:38:00Z
---

# Spatial-Temporal Graph Neural Networks (STGNN)

**Spatial-Temporal Graph Neural Networks (STGNNs)** combine spatial graph convolution operators (to model non-Euclidean station-to-station relationships) with temporal sequential layers (to model time-series evolution).

---

## 1. Graph Construction for Weather Station Networks

Weather stations form a irregular spatial network $\mathcal{G} = (\mathcal{V}, \mathcal{E}, \mathbf{W})$, where:
* $\mathcal{V} = \{v_1, v_2, \dots, v_N\}$ represents $N$ weather stations.
* $\mathbf{W} \in \mathbb{R}^{N \times N}$ is the weighted adjacency matrix based on Haversine geographical distance $d(i, j)$ and elevation differences $\Delta h(i, j)$:

$$W_{ij} = \exp\left( -\left(\frac{d(i, j)}{\sigma_d}\right)^2 - \left(\frac{\Delta h(i, j)}{\sigma_h}\right)^2 \right)$$

Thresholding $W_{ij} < \epsilon$ yields a sparse graph suitable for $O(N+|\mathcal{E}|)$ graph convolution message passing.

---

## 2. GNN Architectures Evaluated

### GraphSAGE (Sample and Aggregate)
Aggregates feature vectors from spatial neighbors using mean, max-pooling, or LSTM aggregators:

$$h_i^{(l+1)} = \sigma\left( \mathbf{W} \cdot \text{CONCAT}\left( h_i^{(l)}, \text{AGGREGATE}\left(\{h_j^{(l)}, \forall j \in \mathcal{N}(i)\}\right) \right) \right)$$

* **Pros**: Scalable to large station networks; inductive learning allows adding new AW stations without retraining the entire graph topology.
* **Cons**: Uniform or simple pooling weights can blur local micro-climate thermal gradients.

### Graph Attention Networks (GAT)
Computes dynamic attention weights $\alpha_{ij}$ between station $i$ and neighboring station $j$ based on node features:

$$\alpha_{ij} = \frac{\exp\left(\text{LeakyReLU}\left(\mathbf{a}^T [\mathbf{W}h_i \| \mathbf{W}h_j]\right)\right)}{\sum_{k \in \mathcal{N}(i)} \exp\left(\text{LeakyReLU}\left(\mathbf{a}^T [\mathbf{W}h_i \| \mathbf{W}h_k]\right)\right)}$$

* **Pros**: Dynamically prioritizes stations experiencing similar micro-climatic shifts (e.g. wind front movements).
* **Cons**: Higher memory complexity $O(N \cdot K)$ per multi-head attention block.

### Spatio-Temporal Graph Convolutional Networks (STGCN)
Interleaves 1D temporal convolutions (Gated Linear Units / TCN) with spatial graph convolutions (Chebyshev or GCN layers):

$$\text{ST-Conv Block}: \text{Temporal-Conv} \rightarrow \text{Spatial-Graph-Conv} \rightarrow \text{Temporal-Conv}$$

* **Pros**: Parallelizable training (faster than recurrent LSTM/GRU wrappers); strong spatial-temporal feature extraction.

---

## Related
- [[concepts/liquid-neural-networks]]
- [[concepts/lfm-vs-baseline-comparison]]
- [[concepts/system-architecture]]
