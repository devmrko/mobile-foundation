"""Read the development guide shipped with the installed Foundation version."""

from importlib.resources import files


def main() -> None:
    print(files("mobile_foundation").joinpath("DEVELOPMENT.md").read_text(encoding="utf-8"), end="")


if __name__ == "__main__":
    main()
