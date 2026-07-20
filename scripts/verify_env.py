import sys

def verify_environment():
    print("=== Environment Verification ===")
    print("Python Version:", sys.version)

    modules = [
        "torch",
        "numpy",
        "pandas",
        "scipy",
        "sklearn",
        "fastapi",
        "pydantic"
    ]

    for mod in modules:
        try:
            m = __import__(mod)
            ver = getattr(m, "__version__", "installed")
            print(f"[OK] {mod}: {ver}")
        except ImportError as e:
            print(f"[FAIL] {mod}: {e}")

    # Test optional torch_geometric & ncps
    try:
        import torch_geometric
        print(f"[OK] torch_geometric: {torch_geometric.__version__}")
    except ImportError:
        print("[WARN] torch_geometric not installed yet in current python environment.")

    try:
        import ncps
        print(f"[OK] ncps: {ncps.__version__}")
    except ImportError:
        print("[WARN] ncps (Liquid Neural Networks) not installed yet in current python environment.")

if __name__ == "__main__":
    verify_environment()
