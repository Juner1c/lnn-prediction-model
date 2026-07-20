import time
import requests

def verify_deployment(host: str = "http://127.0.0.1:8000", retries: int = 5, delay: int = 2) -> bool:
    """
    Automated health check verification script for LNN Heat Index deployment.
    """
    health_url = f"{host}/health"
    dashboard_url = f"{host}/"

    print(f"=== Verifying LNN Service Deployment at {host} ===")

    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(health_url, timeout=5)
            if resp.status_code == 200:
                print(f"[SUCCESS] Health check passed on attempt {attempt}: {resp.json()}")
                
                dash_resp = requests.get(dashboard_url, timeout=5)
                if dash_resp.status_code == 200:
                    print(f"[SUCCESS] Command Center Dashboard accessible at {dashboard_url}")
                    return True
        except Exception as e:
            print(f"[ATTEMPT {attempt}/{retries}] Waiting for server... ({str(e)})")
            time.sleep(delay)

    print("[ERROR] Service deployment verification failed.")
    return False

if __name__ == "__main__":
    verify_deployment()
