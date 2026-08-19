from __future__ import annotations

import csv, io, math, re, statistics, hashlib
from datetime import datetime, timezone
from typing import Any, Literal

import cv2
import numpy as np
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sklearn.linear_model import Ridge, HuberRegressor
from sklearn.model_selection import LeaveOneOut, cross_val_predict
from sklearn.metrics import mean_absolute_error

APP_VERSION = "1.0.0"
PHYSICS_VERSION = "fdm-linear-shrinkage-1.0"
ALGORITHM_VERSION = "deterministic-sim2real-1.0"

app = FastAPI(title="Fabrient Engineering API", version=APP_VERSION)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET", "POST"], allow_headers=["*"])

class EngineeringInput(BaseModel):
    nominal_mm: float = Field(gt=0)
    material: str = Field(min_length=1)
    machine: str = Field(min_length=1)
    process_temperature_c: float = Field(gt=0, lt=400)
    ambient_temperature_c: float = Field(default=23, gt=-50, lt=100)
    nominal_shrinkage_pct: float = Field(default=0.5, ge=0, le=10)
    shrinkage_uncertainty_pct: float = Field(default=0.15, ge=0, le=5)
    tolerance_lower_mm: float = 0
    tolerance_upper_mm: float = 0
    feature_axis: Literal["x", "y", "z"] = "x"

class Observation(BaseModel):
    predicted_mm: float
    measured_mm: float
    machine_id: str | None = None
    feature_id: str | None = None
    context: dict[str, Any] = {}

class CalibrationRequest(BaseModel):
    observations: list[Observation]
    min_validation_points: int = Field(default=3, ge=2, le=20)

class ReverificationInput(BaseModel):
    tolerance_band_mm: float = Field(gt=0)
    uses_per_week: float = Field(ge=0)
    environment_severity: float = Field(ge=0, le=1)
    observed_drift_mm_per_day: float = Field(ge=0)
    consequence_severity: float = Field(ge=0, le=1)
    service_wear_mm_per_day: float = Field(default=0, ge=0)
    measurement_uncertainty_mm: float = Field(default=0, ge=0)

class SimulationInput(BaseModel):
    nominal_mm: float = Field(gt=0)
    shrinkage_pct: float = Field(ge=0, le=10)
    shrinkage_sigma_pct: float = Field(ge=0, le=5)
    temperature_c: float = Field(gt=0, lt=400)
    temperature_sigma_c: float = Field(ge=0, le=50)
    n: int = Field(default=1000, ge=100, le=10000)
    seed: int = 42

class ExperimentInput(BaseModel):
    features: list[dict[str, float]]
    current_uncertainty: dict[str, float] = {}
    budget: float = Field(default=1, ge=0)

class AcceptanceInput(BaseModel):
    nominal_mm: float = Field(gt=0)
    lower_tol_mm: float
    upper_tol_mm: float
    observed_sigma_mm: float = Field(ge=0)
    measurement_sigma_mm: float = Field(ge=0)
    n_observations: int = Field(ge=0)

class UncertaintyInput(BaseModel):
    physics_sigma_mm: float = Field(default=0.0, ge=0)
    measurement_sigma_mm: float = Field(default=0.0, ge=0)
    model_sigma_mm: float = Field(default=0.0, ge=0)
    n_observations: int = Field(default=0, ge=0)

class AgentRequest(BaseModel):
    project_id: str
    objective: str
    max_iterations: int = Field(default=5, ge=1, le=20)

# Existing route implementations continue below.
