# ruff: noqa: F403, F405
from app.sim2real import *
from app.importer import preview_csv,confirm_rows
from app.geometry import parse_stl_ascii
from app.ml import holdout_validate

def test_physics_and_gate():
    s=ProcessState('PETG',240,80,.2,80)
    p=physics_baseline(40,.5,s)
    assert p.nominal_mm < 40
    assert acceptance(p,40,.5)['status']=='insufficient_evidence'

def test_import_messy():
    p=preview_csv('Serial Number,Required,Measured, +/-\nA-1,40,39.8,0.5\n')
    rows=confirm_rows(p)
    assert rows[0]['serial']=='A-1' and rows[0]['actual_mm']==39.8

def test_stl_bounds():
    d=b'''solid x\nfacet normal 0 0 1\nouter loop\nvertex 0 0 0\nvertex 10 0 0\nvertex 0 20 0\nendloop\nendfacet\nendsolid x'''
    g=parse_stl_ascii(d)
    assert g.bounds_mm==(10.0,20.0,0.0)

def test_small_ml_refuses_validation():
    r=holdout_validate([[1],[2],[3],[4],[5]],[1,2,3,4,5])
    assert r.calibrated is False
