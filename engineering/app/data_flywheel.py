from __future__ import annotations
import hashlib,json,os
from datetime import datetime,timezone
from typing import Any
import requests
from fastapi import APIRouter,Header,HTTPException
from pydantic import BaseModel,Field
router=APIRouter(prefix='/data-flywheel',tags=['data-flywheel'])
# Accept the canonical production names plus legacy aliases used by older Render
# environments. Prefer the service-role credential because the flywheel writes
# to protected tables; never require a client-side NEXT_PUBLIC key for writes.
SUPABASE_URL=(os.getenv('SUPABASE_URL') or os.getenv('NEXT_PUBLIC_SUPABASE_URL') or '').strip().rstrip('/')
SUPABASE_KEY=(os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY') or '').strip()
INGEST_SECRET=os.getenv('DATA_FLYWHEEL_INGEST_SECRET')
SOURCES='''user_requirements board_dimensions enclosure_dimensions component_locations connector_locations mounting_holes clearance_requirements wall_thickness fastener_selection material_selection manufacturing_method printer_parameters design_revisions validation_results failed_validations engineer_overrides engineer_corrections accepted_recommendations rejected_recommendations manual_edits print_outcomes measured_dimensions warping_measurements fit_tests assembly_results connector_accessibility fastener_fit pcb_insertion component_interference cable_routing thermal_results vibration_results structural_results manufacturing_defects rework_records scrap_records prototype_iterations time_to_success production_results prediction_measurement_delta step_geometry stl_geometry cad_features hole_patterns fillet_patterns wall_distributions clearance_distributions overhang_distributions interference_patterns assembly_relationships successful_geometry_patterns failure_geometry_patterns manufacturing_geometry_patterns cad_version_diffs feature_failure_locations mcp_success mcp_failure mcp_latency mcp_retries mcp_inputs mcp_outputs invalid_inputs workflow_failures app_crashes ui_abandonment repeated_actions unused_features used_features common_workflows error_messages support_requests feature_requests customer_complaints customer_corrections consented_workflow_events reported_manufacturing_problems reported_time_savings reported_accuracy retention expansion public_standards manufacturer_datasheets application_notes manufacturing_guidelines engineering_papers public_cad_examples open_hardware failure_case_studies printing_research materials_data prediction_reality false_positives false_negatives regression_tests edge_case_discovery confidence_calibration failure_clustering version_comparison new_checks closed_loop'''.split()
class Observation(BaseModel):
 source_key:str; event_type:str; project_id:str|None=None; entity_type:str|None=None; entity_id:str|None=None
 raw_payload:dict[str,Any]=Field(default_factory=dict); normalized_payload:dict[str,Any]=Field(default_factory=dict); provenance:dict[str,Any]=Field(default_factory=dict)
 consent_state:str='unknown'; observed_at:datetime|None=None
def headers():
 if not SUPABASE_URL or not SUPABASE_KEY: raise HTTPException(503,'Supabase service credentials are not configured')
 return {'apikey':SUPABASE_KEY,'Authorization':f'Bearer {SUPABASE_KEY}','Content-Type':'application/json'}
def auth(secret):
 if INGEST_SECRET and secret!=INGEST_SECRET: raise HTTPException(401,'Invalid ingestion secret')
def post(table,payload):
 r=requests.post(f'{SUPABASE_URL}/rest/v1/{table}',headers={**headers(),'Prefer':'return=representation'},json=payload,timeout=20)
 if r.status_code>=300: raise HTTPException(502,f'Supabase write failed: {r.text[:500]}')
 d=r.json(); return d[0] if isinstance(d,list) and d else d
def query(table,filters=None,limit=1000):
 params={"select":"*","limit":str(min(max(limit,1),1000))}
 for key,value in (filters or {}).items():
  if value is not None: params[key]=f"eq.{value}"
 try:
  r=requests.get(f'{SUPABASE_URL}/rest/v1/{table}',headers=headers(),params=params,timeout=20)
  if r.status_code>=300: raise RuntimeError(f'Supabase query failed: {r.status_code}')
  return r.json()
 except requests.RequestException as exc:
  raise RuntimeError('Supabase query unavailable') from exc
@router.get('/catalog')
def catalog(): return {'count':len(SOURCES),'sources':SOURCES}
@router.post('/ingest')
def ingest(o:Observation,x_fabrient_ingest_secret:str|None=Header(default=None)):
 auth(x_fabrient_ingest_secret)
 if o.source_key not in SOURCES: raise HTTPException(400,'Unknown source_key')
 if o.consent_state not in {'allowed','not_applicable'}: raise HTTPException(400,'Consent required')
 payload=o.normalized_payload or o.raw_payload
 h=hashlib.sha256(json.dumps({'s':o.source_key,'e':o.event_type,'p':payload},sort_keys=True,separators=(',',':')).encode()).hexdigest()
 row=post('data_observations',{'project_id':o.project_id,'source_key':o.source_key,'observed_at':(o.observed_at or datetime.now(timezone.utc)).isoformat(),'entity_type':o.entity_type,'entity_id':o.entity_id,'event_type':o.event_type,'raw_payload':o.raw_payload,'normalized_payload':o.normalized_payload,'provenance':o.provenance,'consent_state':o.consent_state,'validation_state':'validated','quality_score':1.0,'content_hash':h})
 return {'accepted':True,'observation_id':row.get('id'),'source_key':o.source_key}
@router.post('/seed-catalog')
def seed_catalog(x_fabrient_ingest_secret:str|None=Header(default=None)):
 auth(x_fabrient_ingest_secret); count=0
 for key in SOURCES:
  r=requests.post(f'{SUPABASE_URL}/rest/v1/data_sources',headers={**headers(),'Prefer':'resolution=merge-duplicates'},json={'key':key,'name':key.replace('_',' ').title(),'category':'data_flywheel','description':f'Fabrient data source: {key}','collection_mode':'event','enabled':True,'consent_required':True,'priority':90 if key in {'prediction_reality','closed_loop','engineer_corrections','print_outcomes','measured_dimensions','false_negatives'} else 50})
  if r.status_code>=300: raise HTTPException(502,f'Catalog seed failed: {r.text[:500]}')
  count+=1
 return {'count':count}
