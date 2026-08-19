"""Deterministic FDM sim-to-real primitives. No synthetic observations are treated as ground truth."""
from __future__ import annotations
from dataclasses import dataclass
from math import sqrt
from statistics import mean, pstdev
from typing import Iterable

@dataclass(frozen=True)
class ProcessState:
    material: str
    nozzle_temp_c: float
    bed_temp_c: float
    layer_height_mm: float
    print_speed_mm_s: float
    ambient_temp_c: float = 23.0
    humidity_pct: float = 50.0

@dataclass(frozen=True)
class Prediction:
    nominal_mm: float
    low_mm: float
    high_mm: float
    physics_sigma_mm: float
    residual_mm: float
    state: str
    provenance: dict

MATERIAL_SHRINKAGE = {"PLA": 0.0025, "PETG": 0.0040, "ABS": 0.0080, "ASA": 0.0070, "TPU": 0.0045}

def validate_inputs(nominal_mm: float, tolerance_mm: float, state: ProcessState) -> None:
    if not 0 < nominal_mm <= 1000: raise ValueError("nominal dimension outside supported range")
    if not 0 < tolerance_mm <= nominal_mm: raise ValueError("invalid tolerance")
    if state.material.upper() not in MATERIAL_SHRINKAGE: raise ValueError("unsupported material: no validated baseline")
    if not 0 < state.layer_height_mm <= 1.0: raise ValueError("layer height outside supported range")
    if not 10 <= state.print_speed_mm_s <= 500: raise ValueError("print speed outside supported range")

def physics_baseline(nominal_mm: float, tolerance_mm: float, state: ProcessState) -> Prediction:
    validate_inputs(nominal_mm, tolerance_mm, state)
    k = MATERIAL_SHRINKAGE[state.material.upper()]
    temp_term = (state.nozzle_temp_c - 210.0) * 0.000002
    ambient_term = (state.ambient_temp_c - 23.0) * 0.00002
    humidity_term = max(0.0, state.humidity_pct - 50.0) * 0.000005
    predicted = nominal_mm * (1.0 - k + temp_term + ambient_term + humidity_term)
    sigma = max(0.015, nominal_mm * (0.25 * k) + tolerance_mm * 0.15)
    return Prediction(predicted, predicted - 1.96*sigma, predicted + 1.96*sigma, sigma, 0.0,
                      "not_calibrated", {"source":"deterministic_physics", "material":state.material.upper(), "algorithm_version":"sim2real-1.0"})

def residual_fit(predicted: Iterable[float], actual: Iterable[float]) -> dict:
    p, a = list(predicted), list(actual)
    if len(p) != len(a) or len(p) < 3: raise ValueError("at least 3 paired real observations are required")
    residuals = [y-x for x,y in zip(p,a)]
    mu = mean(residuals)
    sigma = pstdev(residuals) if len(residuals)>1 else 0.0
    # Leave-one-out errors give an honest small-data validation signal.
    loo = []
    for i in range(len(residuals)):
        train=[residuals[j] for j in range(len(residuals)) if j!=i]
        estimate=mean(train)
        loo.append(abs((residuals[i])-estimate))
    return {"residual_mean_mm":mu,"residual_sigma_mm":sigma,"mae_loo_mm":mean(loo),"n":len(residuals),"validated":len(residuals)>=10}

def apply_calibration(base: Prediction, fit: dict) -> Prediction:
    if not fit or fit.get("n",0) < 3: return base
    residual=float(fit["residual_mean_mm"])
    sigma=sqrt(base.physics_sigma_mm**2 + float(fit.get("residual_sigma_mm",0))**2)
    state="validated" if fit.get("validated") else "limited"
    return Prediction(base.nominal_mm+residual, base.nominal_mm+residual-1.96*sigma, base.nominal_mm+residual+1.96*sigma,
                       sigma,residual,state,{**base.provenance,"calibration_n":fit["n"],"residual_model":"robust_mean"})

def acceptance(pred: Prediction, nominal_mm: float, tolerance_mm: float) -> dict:
    band_low, band_high = nominal_mm-tolerance_mm, nominal_mm+tolerance_mm
    supported = pred.low_mm >= band_low and pred.high_mm <= band_high
    if pred.state == "not_calibrated": return {"status":"insufficient_evidence","reason":"real calibration data is required before a confident acceptance decision"}
    if not supported: return {"status":"refuse","reason":"prediction interval crosses the acceptance boundary","supported_band":[band_low,band_high]}
    return {"status":"pass","reason":"validated interval remains inside acceptance band","supported_band":[band_low,band_high]}

def choose_next_experiment(features: list[dict]) -> dict:
    if not features: raise ValueError("no features available")
    target=max(features,key=lambda x: float(x.get("uncertainty_mm",0)))
    return {"feature":target["name"],"reason":"highest measured predictive uncertainty","expected_information_gain":float(target.get("uncertainty_mm",0))}

def reverification_interval_days(tolerance_mm: float, drift_rate_mm_day: float, use_per_day: float, environment_factor: float, consequence_factor: float) -> dict:
    if tolerance_mm <= 0 or drift_rate_mm_day < 0: raise ValueError("invalid interval inputs")
    if drift_rate_mm_day == 0: return {"status":"insufficient_data","interval_days":None,"reason":"no observed production drift rate"}
    # Half-band reserve; factors are explicit multipliers, never hidden.
    raw=(0.5*tolerance_mm)/(drift_rate_mm_day*max(use_per_day,0.01)*max(environment_factor,0.1)*max(consequence_factor,0.1))
    days=max(1,min(365,round(raw)))
    return {"status":"supported","interval_days":days,"inputs":{"tolerance_mm":tolerance_mm,"drift_rate_mm_day":drift_rate_mm_day,"use_per_day":use_per_day,"environment_factor":environment_factor,"consequence_factor":consequence_factor}}
