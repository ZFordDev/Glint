"""Legacy updater placeholder.

The unreleased updater was removed from packaging for 1.0 because installing
updates is now delegated to each platform's package manager.
"""


def main() -> int:
    print("Update Glint through the package source used to install it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
