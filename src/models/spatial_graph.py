import numpy as np
import pandas as pd
import torch
from typing import Tuple

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on the Earth in kilometers.
    """
    R = 6371.0  # Earth radius in kilometers

    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)

    a = (np.sin(dlat / 2.0) ** 2 +
         np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon / 2.0) ** 2)
    c = 2.0 * np.arctan2(np.sqrt(a), np.sqrt(1.0 - a))
    return float(R * c)

def build_spatial_adjacency_matrix(
    locations_df: pd.DataFrame,
    sigma: float = 15.0,
    max_dist: float = 60.0
) -> Tuple[torch.Tensor, np.ndarray]:
    """
    Construct spatial distance matrix and normalized Gaussian thresholded adjacency matrix.
    A_ij = exp(-d_ij^2 / sigma^2) for d_ij <= max_dist, else 0.
    """
    num_nodes = len(locations_df)
    dist_matrix = np.zeros((num_nodes, num_nodes), dtype=np.float32)

    lats = locations_df["latitude"].values if "latitude" in locations_df.columns else locations_df["lat"].values
    lons = locations_df["longitude"].values if "longitude" in locations_df.columns else locations_df["lon"].values
    elevs = locations_df["elevation"].values / 1000.0 if "elevation" in locations_df.columns else np.zeros(num_nodes)

    for i in range(num_nodes):
        for j in range(num_nodes):
            if i != j:
                d_2d = haversine_distance(lats[i], lons[i], lats[j], lons[j])
                dz = float(abs(elevs[i] - elevs[j]))
                d_3d = float(np.sqrt(d_2d ** 2 + dz ** 2))
                dist_matrix[i, j] = d_3d


    # Gaussian kernel thresholding
    adj = np.zeros((num_nodes, num_nodes), dtype=np.float32)
    for i in range(num_nodes):
        for j in range(num_nodes):
            if i == j:
                adj[i, j] = 1.0  # Self-loop
            elif dist_matrix[i, j] <= max_dist:
                adj[i, j] = np.exp(- (dist_matrix[i, j] ** 2) / (sigma ** 2))

    # Symmetric degree normalization: D^(-1/2) A D^(-1/2)
    deg = np.sum(adj, axis=1)
    deg_inv_sqrt = np.power(deg, -0.5)
    deg_inv_sqrt[np.isinf(deg_inv_sqrt)] = 0.0
    D_mat = np.diag(deg_inv_sqrt)

    norm_adj = D_mat @ adj @ D_mat
    return torch.from_numpy(norm_adj.astype(np.float32)), dist_matrix
