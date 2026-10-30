
import subprocess
import sys


def run_step(description, command):
    print("\n" + "=" * 60)
    print(description)
    print("=" * 60)

    result = subprocess.run(
        [sys.executable, "-m", command],
        check=False
    )

    if result.returncode != 0:
        print(f"\nFAILED: {description}")
        sys.exit(result.returncode)

    print(f"\nSUCCESS: {description}")


def main():
    print("SUPPLIER RELIABILITY SYSTEM")
    print("Starting complete project pipeline...")

    steps = [
        ("Generate supplier datasets", "src.generate_data"),
        ("Validate generated data", "src.validation"),
        ("Calculate supplier scores", "src.scoring"),
        ("Evaluate system performance", "src.evaluation"),
        ("Create SQLite database and SQL export", "src.database"),
    ]

    for description, command in steps:
        run_step(description, command)

    print("\n" + "=" * 60)
    print("PROJECT PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 60)


if __name__ == "__main__":
    main()
