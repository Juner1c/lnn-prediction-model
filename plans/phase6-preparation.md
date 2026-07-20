# Implementation Plan: Phase 6 (Spatial-Temporal GNN Core)

Phase 6 constructs the **Spatial-Temporal Graph Neural Network (STGNN) Forecasting Engine** to model spatial correlations across weather stations in Central Luzon and predict multi-step Heat Index trends.

---

## Objectives of Phase 6

1. **Spatial Adjacency Matrix Builder (`src/models/spatial_graph.py`)**:
   - Computes pairwise Haversine distances between all 7 weather stations from `data/locations.csv`.
   - Applies Gaussian thresholded kernel $A_{ij} = \exp(-d_{ij}^2 / \sigma^2)$ for $d_{ij} \le d_{\text{max}}$, producing a normalized spatial adjacency matrix $A$.
2. **Spatial-Temporal GNN Model (`src/models/stgnn_forecaster.py`)**:
   - `SpatialTemporalGNN`: Combines spatial graph convolution (neighbor aggregation via adjacency $A$) with temporal LNN/RNN sequence processing.
   - Accepts multi-station denoised telemetry tensor `[batch_size, num_nodes=7, seq_len=96, in_channels=5]` and forecasts multi-step Heat Index trajectories `[batch_size, num_nodes=7, forecast_horizon=16]`.
3. **Automated Unit Tests (`tests/test_stgnn_forecaster.py`)**:
   - `unittest` suite validating Haversine distance computations, adjacency matrix symmetry and diagonal properties, GNN tensor dimensions, and forecast outputs.
4. **Knowledge Vault Preservation**:
   - Create `obsidian-vault/concepts/stgnn-forecast-engine.md`.
   - Update `index.md`, `log.md`, and `hot.md`.

---

## Component Details

### `src/models/spatial_graph.py`
- `build_spatial_adjacency_matrix(locations_df, sigma=10.0, max_dist=50.0)` -> `torch.Tensor` ($7 \times 7$).

### `src/models/stgnn_forecaster.py`
- `SpatialGraphConv`: Graph convolution layer $H^{(l+1)} = \text{ReLU}(D^{-1/2} A D^{-1/2} H^{(l)} W)$.
- `SpatialTemporalGNN`: Joint Spatial-Temporal model architecture.

### `tests/test_stgnn_forecaster.py`
- Tests adjacency matrix shape ($7 \times 7$), non-negativity, self-loops, and GNN forward pass shape `[1, 7, 16]`.

---

## Verification Plan

### Automated Verification
- Run `python -m unittest discover tests` (100% test pass rate).

### Knowledge Vault Update
- Create `obsidian-vault/concepts/stgnn-forecast-engine.md`.
- Update `index.md`, `log.md`, and `hot.md`.
