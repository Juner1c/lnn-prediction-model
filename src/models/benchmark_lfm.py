import time
import torch
import numpy as np
from src.models.lfm_denoiser import LiquidDenoisingService

def benchmark_lfm_inference(num_iterations: int = 1000, seq_len: int = 96, batch_size: int = 1):
    """
    Benchmark Liquid Denoising Service inference latency per station.
    Target SLA: < 50 ms per station for a 24-hour (96 x 15-min steps) sequence.
    """
    print(f"=== Benchmarking LNN Denoising Service ===")
    print(f"Parameters: Batch Size={batch_size}, Sequence Length={seq_len} (24h at 15-min step)")

    model = LiquidDenoisingService(input_size=5, hidden_size=32, output_size=5)
    model.eval()

    # Generate dummy input: [batch_size, seq_len, 5]
    x = torch.randn(batch_size, seq_len, 5)

    # Warmup
    with torch.no_grad():
        for _ in range(50):
            _ = model(x)

    latencies_ms = []

    with torch.no_grad():
        for _ in range(num_iterations):
            start = time.perf_counter()
            _ = model(x)
            end = time.perf_counter()
            latencies_ms.append((end - start) * 1000.0)

    mean_lat = np.mean(latencies_ms)
    std_lat = np.std(latencies_ms)
    p99_lat = np.percentile(latencies_ms, 99)
    max_lat = np.max(latencies_ms)

    print(f"\n--- Latency Benchmark Results ({num_iterations} runs) ---")
    print(f"Mean Latency: {mean_lat:.3f} ms")
    print(f"Std Dev:      {std_lat:.3f} ms")
    print(f"P99 Latency:  {p99_lat:.3f} ms")
    print(f"Max Latency:  {max_lat:.3f} ms")
    print(f"SLA Target:   < 50.000 ms")

    is_compliant = p99_lat < 50.0
    print(f"SLA Compliance Status: {'PASSED (COMPLIANT)' if is_compliant else 'FAILED'}")

    return {
        "mean_ms": float(mean_lat),
        "p99_ms": float(p99_lat),
        "max_ms": float(max_lat),
        "is_compliant": is_compliant
    }

if __name__ == "__main__":
    benchmark_lfm_inference()
