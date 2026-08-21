from __future__ import annotations

from dataclasses import dataclass
import numpy as np

TARGET_MAPE_PERCENT = 2.0  # 98% accuracy target
MAX_CORRECTION_FACTOR = 0.05
MAX_ROUNDS = 5
MIN_OBSERVATIONS = 10
HOLDOUT_FRACTION = 0.20


@dataclass
class Fit:
    bias: float
    scale: float
    mae: float
    mape: float


def _validate(predicted, measured):
    p = np.asarray(predicted, dtype=float)
    y = np.asarray(measured, dtype=float)
    if len(p) < MIN_OBSERVATIONS or len(p) != len(y):
        raise ValueError(f"at least {MIN_OBSERVATIONS} paired real observations required")
    if not np.isfinite(p).all() or not np.isfinite(y).all() or (p <= 0).any() or (y <= 0).any():
        raise ValueError("predicted and measured values must be finite and positive")
    return p, y


def _fit_train(p, y) -> tuple[float, float]:
    A = np.column_stack([p, np.ones(len(p))])
    scale, bias = np.linalg.lstsq(A, y, rcond=None)[0]
    scale = float(np.clip(scale, 1 - MAX_CORRECTION_FACTOR, 1 + MAX_CORRECTION_FACTOR))
    bias = float(bias)
    return scale, bias


def _metrics(predicted, measured) -> tuple[float, float]:
    p = np.asarray(predicted, dtype=float)
    y = np.asarray(measured, dtype=float)
    err = p - y
    mae = float(np.mean(np.abs(err)))
    mape = float(np.mean(np.abs(err) / np.maximum(np.abs(y), 1e-9)) * 100)
    return mae, mape


def fit(predicted, measured) -> Fit:
    p, y = _validate(predicted, measured)
    scale, bias = _fit_train(p, y)
    corrected = p * scale + bias
    mae, mape = _metrics(corrected, y)
    return Fit(bias, scale, mae, mape)


def _holdout_split(p, y):
    # Deterministic tail holdout: never optimize against the evidence used to score release accuracy.
    n = len(p)
    holdout_n = max(2, int(np.ceil(n * HOLDOUT_FRACTION)))
    if n - holdout_n < 5:
        holdout_n = max(1, n - 5)
    return p[:-holdout_n], y[:-holdout_n], p[-holdout_n:], y[-holdout_n:]


def auto_fix(predicted, measured, max_rounds=MAX_ROUNDS):
    p, y = _validate(predicted, measured)
    train_p, train_y, hold_p, hold_y = _holdout_split(p, y)
    history = []

    # Fit once on the training partition. The correction is explicitly bounded by
    # MAX_CORRECTION_FACTOR; repeatedly fitting the already-corrected data could
    # compound corrections and make a large real error appear falsely validated.
    scale, bias = _fit_train(train_p, train_y)
    corrected_train = train_p * scale + bias
    corrected_hold = hold_p * scale + bias
    train_mae, train_mape = _metrics(corrected_train, train_y)
    hold_mae, hold_mape = _metrics(corrected_hold, hold_y)
    history.append({
        "round": 1,
        "scale": scale,
        "bias_mm": bias,
        "train_mae_mm": train_mae,
        "train_mape_percent": train_mape,
        "held_out_mae_mm": hold_mae,
        "held_out_mape_percent": hold_mape,
        "correction_bound_percent": MAX_CORRECTION_FACTOR * 100,
    })
    return Fit(bias, scale, hold_mae, hold_mape), history, hold_mape <= TARGET_MAPE_PERCENT

