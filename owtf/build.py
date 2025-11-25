from pathlib import Path
from subprocess import call

from setuptools.command.develop import develop
from setuptools.command.install import install


ROOT_DIR = Path(__file__).resolve().parent.parent
POST_SCRIPT = ROOT_DIR / "scripts" / "install.sh"


def _run_post_install() -> None:
    """Run the post installation script."""
    print("Running post install")
    call(["/bin/bash", str(POST_SCRIPT)])


class PostDevelopCommand(develop):
    """Post-installation for development mode."""

    def run(self) -> None:  # type: ignore[override]
        super().run()
        _run_post_install()


class PostInstallCommand(install):
    """Post-installation for installation mode."""

    def run(self) -> None:  # type: ignore[override]
        installer = getattr(self, "do_egg_install", None)
        if callable(installer):
            installer()
        else:
            super().run()
        _run_post_install()
