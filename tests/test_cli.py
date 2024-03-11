"""Test commandline interface."""

from pathlib import Path

from ase.io import read
from typer.testing import CliRunner

from janus_core.cli import app

DATA_PATH = Path(__file__).parent / "data"

runner = CliRunner()


def test_janus_help():
    """Test calling `janus --help`."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    # Command is returned as "root"
    assert "Usage: root [OPTIONS] COMMAND [ARGS]..." in result.stdout


def test_singlepoint_help():
    """Test calling `janus singlepoint --help`."""
    result = runner.invoke(app, ["singlepoint", "--help"])
    assert result.exit_code == 0
    # Command is returned as "root"
    assert "Usage: root singlepoint [OPTIONS]" in result.stdout


def test_singlepoint(tmp_path):
    """Test singlepoint calculation."""
    results_path = tmp_path / "NaCl-results.xyz"

    result = runner.invoke(
        app,
        [
            "singlepoint",
            "--struct",
            DATA_PATH / "NaCl.cif",
            "--write-kwargs",
            f"{{'filename': '{str(results_path)}'}}",
        ],
    )
    assert result.exit_code == 0

    atoms = read(results_path)
    assert atoms.get_potential_energy() is not None
    assert "forces" in atoms.arrays


def test_singlepoint_properties(tmp_path):
    """Test properties for singlepoint calculation."""
    results_path = tmp_path / "H2O-results.xyz"

    # Check energy is can be calculated successfully
    result = runner.invoke(
        app,
        [
            "singlepoint",
            "--struct",
            DATA_PATH / "H2O.cif",
            "--property",
            "energy",
            "--write-kwargs",
            f"{{'filename': '{str(results_path)}'}}",
        ],
    )
    assert result.exit_code == 0

    atoms = read(results_path)
    results_path.unlink()
    assert atoms.get_potential_energy() is not None

    result = runner.invoke(
        app,
        [
            "singlepoint",
            "--struct",
            DATA_PATH / "H2O.cif",
            "--property",
            "stress",
            "--write-kwargs",
            f"{{'filename': '{str(results_path)}'}}",
        ],
    )
    assert result.exit_code == 1
    assert not results_path.is_file()
    assert isinstance(result.exception, ValueError)


def test_singlepoint_read_kwargs(tmp_path):
    """Test setting read_kwargs for singlepoint calculation."""
    results_path = tmp_path / "benzene-traj-results.xyz"

    result = runner.invoke(
        app,
        [
            "singlepoint",
            "--struct",
            DATA_PATH / "benzene-traj.xyz",
            "--read-kwargs",
            "{'index': ':'}",
            "--write-kwargs",
            f"{{'filename': '{str(results_path)}'}}",
            "--property",
            "energy",
        ],
    )
    assert result.exit_code == 0

    atoms = read(results_path, index=":")
    assert isinstance(atoms, list)


def test_singlepoint_calc_kwargs(tmp_path):
    """Test setting calc_kwargs for singlepoint calculation."""
    results_path = tmp_path / "NaCl-results.xyz"

    result = runner.invoke(
        app,
        [
            "singlepoint",
            "--struct",
            DATA_PATH / "NaCl.cif",
            "--calc-kwargs",
            "{'default_dtype': 'float32'}",
            "--write-kwargs",
            f"{{'filename': '{str(results_path)}'}}",
            "--property",
            "energy",
        ],
    )
    assert result.exit_code == 0
    assert "Using float32 for MACECalculator" in result.stdout


def test_singlepoint_default_write():
    """Test default write path."""
    results_path = Path(".").absolute() / "NaCl-results.xyz"
    assert not results_path.exists()

    result = runner.invoke(
        app,
        [
            "singlepoint",
            "--struct",
            DATA_PATH / "NaCl.cif",
            "--property",
            "energy",
        ],
    )
    assert result.exit_code == 0
    atoms = read(results_path)
    assert "forces" in atoms.arrays

    results_path.unlink()
