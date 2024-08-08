"""Test phonons calculations."""

from pathlib import Path

from ase.io import read
import pytest

from janus_core.calculations.phonons import Phonons
from janus_core.calculations.single_point import SinglePoint
from janus_core.helpers.mlip_calculators import choose_calculator
from tests.utils import assert_log_contains

DATA_PATH = Path(__file__).parent / "data"
MODEL_PATH = Path(__file__).parent / "models" / "mace_mp_small.model"


def test_init():
    """Test initialising Phonons."""
    single_point = SinglePoint(
        struct_path=DATA_PATH / "NaCl.cif",
        arch="mace",
        calc_kwargs={"model": MODEL_PATH},
    )
    phonons = Phonons(struct=single_point.struct)
    assert str(phonons.file_prefix) == "Cl4Na4"


def test_calc_phonons():
    """Test calculating phonons from ASE atoms object."""
    struct = read(DATA_PATH / "NaCl.cif")
    struct.calc = choose_calculator(arch="mace_mp", model=MODEL_PATH)

    phonons = Phonons(
        struct=struct,
    )

    phonons.calc_force_constants(write_force_consts=False)
    assert "phonon" in phonons.results


def test_optimize(tmp_path):
    """Test optimizing structure before calculation."""
    log_file = tmp_path / "phonons.log"
    single_point = SinglePoint(
        struct_path=DATA_PATH / "NaCl.cif",
        arch="mace",
        calc_kwargs={"model": MODEL_PATH},
    )
    phonons = Phonons(
        struct=single_point.struct,
        log_kwargs={"filename": log_file},
        minimize=True,
    )
    phonons.calc_force_constants(write_force_consts=False)

    assert_log_contains(
        log_file,
        includes=["Using filter", "Using optimizer", "Starting geometry optimization"],
    )


def test_invalid_struct():
    """Test setting invalid structure."""
    single_point = SinglePoint(
        struct_path=DATA_PATH / "benzene-traj.xyz",
        arch="mace_mp",
        calc_kwargs={"model": MODEL_PATH},
    )

    with pytest.raises(NotImplementedError):
        Phonons(
            single_point.struct,
        )
    with pytest.raises(ValueError):
        Phonons(
            "structure",
        )
