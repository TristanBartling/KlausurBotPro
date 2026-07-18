"""Compatibility checks for the phase-0.5 technology stack."""

import control
import matplotlib
import numpy as np
import scipy
import sympy as sp
from matplotlib.figure import Figure
from PySide6 import QtCore
from scipy.special import expit

import klausurbotpro.app


def test_library_imports() -> None:
    assert control.__version__
    assert matplotlib.__version__
    assert np.__version__
    assert scipy.__version__
    assert sp.__version__
    assert QtCore.qVersion()
    assert klausurbotpro.app.APP_NAME == "KlausurBotPro"


def test_sympy_factorization() -> None:
    variable = sp.symbols("x")
    assert sp.factor(variable**2 - 1) == (variable - 1) * (variable + 1)


def test_numpy_eigenvalues() -> None:
    matrix = np.array([[2.0, 0.0], [0.0, 3.0]])
    np.testing.assert_allclose(np.sort(np.linalg.eigvals(matrix)), [2.0, 3.0])


def test_scipy_elementary_function() -> None:
    assert expit(0.0) == 0.5


def test_python_control_transfer_function_without_slycot() -> None:
    system = control.tf([1.0], [1.0, 1.0])
    assert system.ninputs == 1
    assert system.noutputs == 1


def test_matplotlib_figure_without_visible_window() -> None:
    assert matplotlib.get_backend().lower() == "agg"
    figure = Figure()
    axes = figure.subplots()
    axes.plot([0.0, 1.0], [0.0, 1.0])
    assert len(figure.axes) == 1
