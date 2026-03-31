import subprocess
import sys
import time


def run_sentinel():
    print("Starting SentinelStock Unified App...")

    # Give the DB a 5-second head start to finish its init script
    time.sleep(5)

    # Start the Ingestor (Piping output so we can see errors)
    ingestor = subprocess.Popen([sys.executable, "injestor.py"])

    # Start the Streamlit Frontend
    frontend = subprocess.Popen(
        [
            "streamlit",
            "run",
            "frontend.py",
            "--server.port=8501",
            "--server.address=0.0.0.0",
        ]
    )

    try:
        while True:
            time.sleep(1)
            # Check if either process has died
            if ingestor.poll() is not None:
                print("Ingestor process died unexpectedly.")
                break
            if frontend.poll() is not None:
                print("Frontend process died unexpectedly.")
                break
    except KeyboardInterrupt:
        print("\nStopping SentinelStock...")
    finally:
        ingestor.terminate()
        frontend.terminate()


if __name__ == "__main__":
    run_sentinel()
