"""Test phonons commandline interface."""

from pathlib import Path

import pytest
from typer.testing import CliRunner
import yaml

from janus_core.cli.janus import app
from tests.utils import assert_log_contains, clear_log_handlers, strip_ansi_codes

DATA_PATH = Path(__file__).parent / "data"

runner = CliRunner()


def test_help():
    """Test calling `janus phonons --help`."""
    result = runner.invoke(app, ["phonons", "--help"])
    assert result.exit_code == 0
    assert "Usage: janus phonons [OPTIONS]" in strip_ansi_codes(result.stdout)


def test_phonons():
    """Test calculating force constants and band structure."""
    phonopy_path = Path("./NaCl-phonopy.yml").absolute()
    bands_path = Path("./NaCl-auto_bands.yml").absolute()
    log_path = Path("./NaCl-phonons-log.yml").absolute()
    summary_path = Path("./NaCl-phonons-summary.yml").absolute()

    assert not phonopy_path.exists()
    assert not bands_path.exists()
    assert not log_path.exists()
    assert not summary_path.exists()

    try:
        result = runner.invoke(
            app,
            [
                "phonons",
                "--struct",
                DATA_PATH / "NaCl.cif",
                "--no-hdf5",
                "--bands",
            ],
        )
        assert result.exit_code == 0

        assert phonopy_path.exists()
        assert bands_path.exists()
        assert log_path.exists()
        assert summary_path.exists()

        # Read phonons summary file
        with open(summary_path, encoding="utf8") as file:
            phonon_summary = yaml.safe_load(file)

        has_eigenvectors = False
        has_velocity = False
        with open(bands_path, encoding="utf8") as file:
            for line in file:
                if "eigenvector" in line:
                    has_eigenvectors = True
                if "group_velocity" in line:
                    has_velocity = True
                if has_eigenvectors and has_velocity:
                    break
        assert has_eigenvectors and has_velocity

        assert "command" in phonon_summary
        assert "janus phonons" in phonon_summary["command"]
        assert "start_time" in phonon_summary
        assert "inputs" in phonon_summary
        assert "end_time" in phonon_summary

        assert "emissions" in phonon_summary
        assert phonon_summary["emissions"] > 0

    finally:
        phonopy_path.unlink(missing_ok=True)
        bands_path.unlink(missing_ok=True)
        log_path.unlink(missing_ok=True)
        summary_path.unlink(missing_ok=True)
        clear_log_handlers()


def test_bands_simple(tmp_path):
    """Test calculating force constants and reduced bands information."""
    file_prefix = tmp_path / "NaCl"
    autoband_results = tmp_path / "NaCl-auto_bands.yml"
    summary_path = tmp_path / "NaCl-phonons-summary.yml"

    result = runner.invoke(
        app,
        [
            "phonons",
            "--struct",
            DATA_PATH / "NaCl.cif",
            "--bands",
            "--no-write-full",
            "--no-hdf5",
            "--file-prefix",
            file_prefix,
        ],
    )
    assert result.exit_code == 0

    assert autoband_results.exists()
    with open(autoband_results, encoding="utf8") as file:
        bands = yaml.safe_load(file)
    assert "eigenvector" not in bands["phonon"][0]["band"][0]

    # Read phonons summary file
    assert summary_path.exists()
    with open(summary_path, encoding="utf8") as file:
        phonon_summary = yaml.safe_load(file)

    assert "command" in phonon_summary
    assert "janus phonons" in phonon_summary["command"]
    assert "inputs" in phonon_summary
    assert "calcs" in phonon_summary["inputs"]
    assert phonon_summary["inputs"]["calcs"][0] == "bands"


def test_hdf5(tmp_path):
    """Test saving force constants to HDF5 in new directory."""
    file_prefix = tmp_path / "test" / "NaCl"
    phonon_results = tmp_path / "test" / "NaCl-phonopy.yml"
    hdf5_results = tmp_path / "test" / "NaCl-force_constants.hdf5"

    result = runner.invoke(
        app,
        [
            "phonons",
            "--struct",
            DATA_PATH / "NaCl.cif",
            "--file-prefix",
            file_prefix,
            "--hdf5",
        ],
    )
    assert result.exit_code == 0
    assert phonon_results.exists()
    assert hdf5_results.exists()


def test_thermal_props(tmp_path):
    """Test calculating thermal properties."""
    file_prefix = tmp_path / "test" / "NaCl"
    thermal_results = tmp_path / "test" / "NaCl-thermal.dat"

    result = runner.invoke(
        app,
        [
            "phonons",
            "--struct",
            DATA_PATH / "NaCl.cif",
            "--thermal",
            "--no-hdf5",
            "--file-prefix",
            file_prefix,
        ],
    )
    assert result.exit_code == 0
    assert thermal_results.exists()


def test_dos(tmp_path):
    """Test calculating the DOS."""
    file_prefix = tmp_path / "test" / "NaCl"
    dos_results = tmp_path / "test" / "NaCl-dos.dat"

    result = runner.invoke(
        app,
        [
            "phonons",
            "--struct",
            DATA_PATH / "NaCl.cif",
            "--dos",
            "--no-hdf5",
            "--file-prefix",
            file_prefix,
        ],
    )
    assert result.exit_code == 0
    assert dos_results.exists()


def test_pdos(tmp_path):
    """Test calculating the PDOS."""
    file_prefix = tmp_path / "test" / "NaCl"
    pdos_results = tmp_path / "test" / "NaCl-pdos.dat"

    result = runner.invoke(
        app,
        [
            "phonons",
            "--struct",
            DATA_PATH / "NaCl.cif",
            "--pdos",
            "--no-hdf5",
            "--file-prefix",
            file_prefix,
        ],
    )
    assert result.exit_code == 0
    assert pdos_results.exists()


def test_plot(tmp_path):
    """Test for plotting routines."""
    file_prefix = tmp_path / "NaCl"
    pdos_results = tmp_path / "NaCl-pdos.dat"
    dos_results = tmp_path / "NaCl-dos.dat"
    autoband_results = tmp_path / "NaCl-auto_bands.yml"
    summary_path = tmp_path / "NaCl-phonons-summary.yml"
    svgs = [
        tmp_path / "NaCl-dos.svg",
        tmp_path / "NaCl-pdos.svg",
        tmp_path / "NaCl-bs-dos.svg",
        tmp_path / "NaCl-auto_bands.svg",
    ]

    result = runner.invoke(
        app,
        [
            "phonons",
            "--struct",
            DATA_PATH / "NaCl.cif",
            "--supercell",
            1,
            1,
            1,
            "--pdos",
            "--dos",
            "--bands",
            "--no-hdf5",
            "--plot-to-file",
            "--no-write-full",
            "--file-prefix",
            file_prefix,
        ],
    )
    assert result.exit_code == 0
    assert pdos_results.exists()
    assert dos_results.exists()
    for svg in svgs:
        assert svg.exists()

    assert autoband_results.exists()

    # Read phonons summary file
    assert summary_path.exists()
    with open(summary_path, encoding="utf8") as file:
        phonon_summary = yaml.safe_load(file)
    assert phonon_summary["inputs"]["calcs"][0] == "bands"
    assert phonon_summary["inputs"]["calcs"][1] == "dos"
    assert phonon_summary["inputs"]["calcs"][2] == "pdos"


def test_supercell(tmp_path):
    """Test setting the supercell."""
    file_prefix = tmp_path / "NaCl"
    param_file = tmp_path / "NaCl-phonopy.yml"

    result = runner.invoke(
        app,
        [
            "phonons",
            "--struct",
            DATA_PATH / "NaCl.cif",
            "--supercell",
            1,
            2,
            3,
            "--no-hdf5",
            "--file-prefix",
            file_prefix,
        ],
    )
    assert result.exit_code == 0

    # Check parameters
    with open(param_file, encoding="utf8") as file:
        params = yaml.safe_load(file)

    assert "supercell_matrix" in params
    assert len(params["supercell_matrix"]) == 3
    assert params["supercell_matrix"] == [[1, 0, 0], [0, 2, 0], [0, 0, 3]]


@pytest.mark.parametrize("supercell", [(2,), (2, 2), (2, 2, "a"), ("2x2x2",)])
def test_invalid_supercell(supercell, tmp_path):
    """Test errors are raise for invalid supercells."""
    file_prefix = tmp_path / "test"

    result = runner.invoke(
        app,
        [
            "phonons",
            "--struct",
            DATA_PATH / "NaCl.cif",
            "--supercell",
            *supercell,
            "--file-prefix",
            file_prefix,
        ],
    )
    assert result.exit_code == 1 or result.exit_code == 2


def test_minimize_kwargs(tmp_path):
    """Test setting optimizer function and writing optimized structure."""
    file_prefix = tmp_path / "test"
    opt_path = tmp_path / "test-opt.extxyz"
    log_path = tmp_path / "test-phonons-log.yml"

    minimize_kwargs = "{'optimizer': 'FIRE', 'write_results': True}"

    result = runner.invoke(
        app,
        [
            "phonons",
            "--struct",
            DATA_PATH / "NaCl.cif",
            "--minimize",
            "--minimize-kwargs",
            minimize_kwargs,
            "--no-hdf5",
            "--file-prefix",
            file_prefix,
        ],
    )
    assert result.exit_code == 0

    assert_log_contains(
        log_path,
        includes=["Starting geometry optimization", "Using optimizer: FIRE"],
    )
    assert opt_path.exists()


def test_minimize_filename(tmp_path):
    """Test minimize filename overwrites default."""
    file_prefix = tmp_path / "test" / "test"
    opt_path = tmp_path / "test" / "geomopt-opt.extxyz"

    # write_results should be set automatically
    minimize_kwargs = f"{{'write_kwargs': {{'filename': '{str(opt_path)}'}}}}"

    result = runner.invoke(
        app,
        [
            "phonons",
            "--struct",
            DATA_PATH / "NaCl.cif",
            "--minimize",
            "--minimize-kwargs",
            minimize_kwargs,
            "--no-hdf5",
            "--file-prefix",
            file_prefix,
        ],
    )
    assert result.exit_code == 0
    assert opt_path.exists()


@pytest.mark.parametrize("read_kwargs", ["{'index': 0}", "{}"])
def test_valid_traj_input(read_kwargs, tmp_path):
    """Test valid trajectory input structure handled."""
    file_prefix = tmp_path / "traj"
    phonon_results = tmp_path / "traj-phonopy.yml"

    result = runner.invoke(
        app,
        [
            "phonons",
            "--struct",
            DATA_PATH / "NaCl-traj.xyz",
            "--supercell",
            1,
            1,
            1,
            "--read-kwargs",
            read_kwargs,
            "--no-hdf5",
            "--file-prefix",
            file_prefix,
        ],
    )
    assert result.exit_code == 0
    assert phonon_results.exists()


def test_invalid_traj_input(tmp_path):
    """Test invalid trajectory input structure handled."""
    file_prefix = tmp_path / "NaCl"

    result = runner.invoke(
        app,
        [
            "phonons",
            "--struct",
            DATA_PATH / "NaCl-traj.xyz",
            "--read-kwargs",
            "{'index': ':'}",
            "--file-prefix",
            file_prefix,
        ],
    )
    assert result.exit_code == 1
    assert isinstance(result.exception, ValueError)


def test_no_carbon(tmp_path):
    """Test disabling carbon tracking."""
    file_prefix = tmp_path / "NaCl"
    summary_path = tmp_path / "NaCl-phonons-summary.yml"

    result = runner.invoke(
        app,
        [
            "phonons",
            "--struct",
            DATA_PATH / "NaCl.cif",
            "--no-hdf5",
            "--no-tracker",
            "--file-prefix",
            file_prefix,
        ],
    )
    assert result.exit_code == 0

    # Read phonons summary file
    with open(summary_path, encoding="utf8") as file:
        phonon_summary = yaml.safe_load(file)
        assert "emissions" not in phonon_summary
