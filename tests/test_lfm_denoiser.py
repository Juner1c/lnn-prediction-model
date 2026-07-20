import unittest
import torch
from src.models.lfm_denoiser import LiquidDenoisingService
from src.models.benchmark_lfm import benchmark_lfm_inference

class TestLiquidDenoisingService(unittest.TestCase):
    def setUp(self):
        self.model = LiquidDenoisingService(input_size=5, hidden_size=32, output_size=5)
        self.model.eval()

    def test_forward_shape(self):
        batch_size, seq_len, features = 4, 96, 5
        x = torch.randn(batch_size, seq_len, features)
        with torch.no_grad():
            out = self.model(x)
        self.assertEqual(out.shape, (batch_size, seq_len, features))

    def test_latency_sla_compliance(self):
        res = benchmark_lfm_inference(num_iterations=100, seq_len=96, batch_size=1)
        self.assertTrue(res["is_compliant"])
        self.assertLess(res["p99_ms"], 50.0)

if __name__ == "__main__":
    unittest.main()
