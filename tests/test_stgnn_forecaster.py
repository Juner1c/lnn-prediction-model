import unittest
import os
import torch
import pandas as pd
from src.models.spatial_graph import haversine_distance, build_spatial_adjacency_matrix
from src.models.stgnn_forecaster import SpatialGraphConv, SpatialTemporalGNN

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

class TestSpatialTemporalGNN(unittest.TestCase):
    def setUp(self):
        self.locations_csv = os.path.join(BASE_DIR, "data", "locations.csv")
        self.df_locs = pd.read_csv(self.locations_csv)
        self.adj_tensor, self.dist_matrix = build_spatial_adjacency_matrix(self.df_locs)


    def test_haversine_distance(self):
        # Subic (14.868, 120.279) to Bataan (14.727, 120.306) -> ~15-20 km
        dist = haversine_distance(14.868190, 120.279594, 14.727592, 120.306980)
        self.assertTrue(10.0 <= dist <= 25.0)

    def test_spatial_adjacency_shape_and_properties(self):
        self.assertEqual(self.adj_tensor.shape, (7, 7))
        # Self-loops should be non-zero
        self.assertTrue(torch.all(self.adj_tensor >= 0.0))

    def test_spatial_graph_conv_shape(self):
        conv = SpatialGraphConv(in_features=5, out_features=16)
        x = torch.randn(2, 7, 5) # batch=2, nodes=7, in=5
        out = conv(x, self.adj_tensor)
        self.assertEqual(out.shape, (2, 7, 16))

    def test_stgnn_forecaster_forward_pass(self):
        model = SpatialTemporalGNN(num_nodes=7, in_channels=5, hidden_dim=32, forecast_horizon=16)
        model.eval()
        x = torch.randn(2, 7, 96, 5) # batch=2, nodes=7, seq=96 (24h), channels=5
        with torch.no_grad():
            forecasts = model(x, self.adj_tensor)
        self.assertEqual(forecasts.shape, (2, 7, 16, 5))

    def test_stgnn_forecaster_autoregressive_rollout(self):
        model = SpatialTemporalGNN(num_nodes=7, in_channels=5, hidden_dim=32, forecast_horizon=16)
        model.eval()
        x = torch.randn(1, 7, 96, 5)
        with torch.no_grad():
            rollout = model.predict_autoregressive_rollout(x, self.adj_tensor, steps=720)
        self.assertEqual(rollout.shape, (1, 7, 720))

if __name__ == "__main__":
    unittest.main()
