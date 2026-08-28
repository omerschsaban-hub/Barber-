'use client';

import {useMemo, useState} from 'react';
import {Canvas} from '@react-three/fiber';
import {Edges, Float, Grid, OrbitControls, Sparkles} from '@react-three/drei';
import * as THREE from 'three';

const ENGINE = '/api/engineering';

type MeshData = {vertices:number[][];triangles:number[][];triangle_count?:number};

type GeometryData = {
  status:string;
  filename?:string;
  bounding_box:{size:number[];units:string};
  brep?:{solids:number;faces:number;edges:number;vertices:number;volume_native_units:number};
  mesh?:MeshData;
  provenance?:Record<string, unknown>;
};

function KernelMesh({mesh}:{mesh:MeshData}){
  const {geometry, scale} = useMemo(() => {
    const g = new THREE.BufferGeometry();
    const raw = mesh.vertices.map(v => new THREE.Vector3(v[0], v[1], v[2]));
    const box = new THREE.Box3().setFromPoints(raw);
    const center = box.getCenter(new THREE.Vector3());
    const size = box.getSize(new THREE.Vector3());
    const maxDimension = Math.max(size.x, size.y, size.z, 0.001);
    const positions = new Float32Array(raw.flatMap(v => [v.x - center.x, v.y - center.y, v.z - center.z]));
    const indices = new Uint32Array(mesh.triangles.flatMap(t => [t[0], t[1], t[2]]));
    g.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    g.setIndex(new THREE.BufferAttribute(indices, 1));
    g.computeVertexNormals();
    g.computeBoundingSphere();
    return {geometry:g, scale:1.8 / maxDimension};
  }, [mesh]);

  return (
    <group scale={scale}>
      <Float speed={1.2} rotationIntensity={0.08} floatIntensity={0.12}>
        <mesh geometry={geometry} castShadow receiveShadow>
          <meshStandardMaterial color="#c47b2c" metalness={0.7} roughness={0.28} side={THREE.DoubleSide} />
          <Edges color="#f2b15d" threshold={18} linewidth={1.2} />
        </mesh>
      </Float>
    </group>
  );
}

function EngineeringStage({mesh}:{mesh:MeshData}){
  return (
    <Canvas shadows camera={{position:[2.8,2.2,2.8], fov:38}} dpr={[1,2]}>
      <color attach="background" args={["#0a0b0d"]} />
      <ambientLight intensity={0.55} />
      <directionalLight position={[3,5,4]} intensity={3.2} castShadow shadow-mapSize={[2048,2048]} />
      <pointLight position={[-3,1,2]} intensity={8} distance={8} color="#d88a3b" />
      <pointLight position={[2,-1,-3]} intensity={4} distance={7} color="#7d8ea3" />
      <Sparkles count={28} scale={[4,2.6,4]} size={1.2} speed={0.25} opacity={0.32} />
      <Grid args={[4,4]} cellSize={0.2} cellThickness={0.45} sectionSize={1} sectionThickness={0.9} fadeDistance={6} fadeStrength={1.4} />
      <KernelMesh mesh={mesh} />
      <OrbitControls enableDamping dampingFactor={0.08} autoRotate autoRotateSpeed={0.65} minDistance={1.7} maxDistance={6} />
    </Canvas>
  );
}

export default function Geometry(){
  const[file,setFile]=useState<File>();
  const[data,setData]=useState<GeometryData>();
  const[error,setError]=useState('');
  const[loading,setLoading]=useState(false);

  async function run(){
    if(!file)return;
    setError('');setLoading(true);setData(undefined);
    try{
      const fd=new FormData();
      fd.append('file',file,file.name);
      const r=await fetch(`${ENGINE}/v1/geometry/step`,{method:'POST',body:fd});
      const j=await r.json().catch(()=>({detail:'Engineering service returned invalid JSON.'}));
      if(!r.ok)throw new Error(j.detail||`Geometry extraction failed (${r.status})`);
      if(!j.bounding_box?.size||j.bounding_box.size.length!==3)throw new Error('STEP response did not contain a verified 3D bounding box.');
      if(!j.mesh?.vertices?.length||!j.mesh?.triangles?.length)throw new Error('STEP extraction succeeded but returned no kernel tessellation for visualization.');
      setData(j);
    }catch(e:any){setError(e?.message||'Geometry extraction failed.');}
    finally{setLoading(false);}
  }

  const size=data?.bounding_box?.size;
  const mesh=data?.mesh;
  const topologyVerified=Boolean(data?.provenance?.topology_verified);

  return <main className="page wide geometry-page">
    <div className="eyebrow">GEOMETRY / STEP</div>
    <div className="geometry-heading">
      <div>
        <h1 className="title">Kernel-verified 3D geometry</h1>
        <p className="muted">A real tessellation from the STEP kernel — not a decorative approximation. Inspect the part, rotate it, and keep the engineering evidence beside the model.</p>
      </div>
      {data&&<div className={`verification-pill ${topologyVerified?'verified':''}`}><span className="verification-dot" />{topologyVerified?'TOPOLOGY VERIFIED':'REVIEW REQUIRED'}</div>}
    </div>

    <div className="workspace-grid geometry-grid">
      <section className="panel input-panel">
        <div className="panel-kicker">01 / INPUT</div>
        <h2>STEP SOURCE</h2>
        <p className="muted small">Upload the authoritative CAD artifact. Fabrient extracts BREP topology and a deterministic OCCT tessellation.</p>
        <label className="dropzone">
          <input type="file" accept=".step,.stp" onChange={e=>setFile(e.target.files?.[0])}/>
          <span className="dropzone-icon">＋</span>
          <strong>{file?.name || 'Choose a STEP file'}</strong>
          <span className="muted small">.STEP / .STP</span>
        </label>
        <button className="button primary geometry-action" disabled={!file||loading} onClick={run}>{loading?'Extracting kernel geometry…':'Extract & visualize'}</button>
        {error&&<p className="error" role="alert">{error}</p>}
        {data&&<div className="geometry-facts">
          <div><span>STATUS</span><strong>{data.status}</strong></div>
          <div><span>TOPOLOGY</span><strong>{data.brep?.solids ?? 0} solids · {data.brep?.faces ?? 0} faces</strong></div>
          <div><span>BOUNDING BOX</span><strong>{size?.map((v:number)=>v.toFixed(3)).join(' × ')} {data.bounding_box.units}</strong></div>
        </div>}
      </section>

      <section className="panel model-panel">
        <div className="model-toolbar">
          <div><div className="panel-kicker">02 / MODEL</div><h2>3D INSPECTION</h2></div>
          {mesh&&<div className="triangle-count">{mesh.triangle_count ?? mesh.triangles.length} TRIANGLES</div>}
        </div>
        {mesh?<div className="viewer viewer-3d"><EngineeringStage mesh={mesh}/><div className="viewer-overlay"><span>OCCT TESSELLATION</span><span>DRAG TO ORBIT · SCROLL TO ZOOM</span></div></div>:<div className="viewer-empty"><div className="empty-ring">3D</div><strong>Verified geometry appears here</strong><span className="muted">Upload a STEP file to replace this placeholder with the actual kernel-derived model.</span></div>}
      </section>
    </div>

    {data&&<section className="panel provenance-panel">
      <div><div className="panel-kicker">03 / EVIDENCE</div><h2>PROVENANCE</h2></div>
      <pre className="provenance">{JSON.stringify(data.provenance,null,2)}</pre>
    </section>}

    <style jsx>{`
      .geometry-page{padding-bottom:64px}
      .geometry-heading{display:flex;align-items:flex-start;justify-content:space-between;gap:24px;margin-bottom:28px}
      .geometry-heading .title{margin-bottom:10px}
      .geometry-heading p{max-width:760px;margin:0}
      .verification-pill{display:flex;align-items:center;gap:8px;border:1px solid rgba(255,255,255,.12);padding:9px 12px;border-radius:999px;font-size:11px;letter-spacing:.08em;white-space:nowrap}
      .verification-pill.verified{border-color:rgba(216,138,59,.45);color:#f2b15d}
      .verification-dot{width:7px;height:7px;border-radius:50%;background:#68717b}
      .verified .verification-dot{background:#e29a50;box-shadow:0 0 12px rgba(226,154,80,.7)}
      .geometry-grid{grid-template-columns:minmax(280px,.72fr) minmax(0,1.7fr);align-items:stretch}
      .input-panel,.model-panel{min-height:570px}
      .panel-kicker{font-size:10px;letter-spacing:.14em;color:#7f8994;margin-bottom:8px}
      .small{font-size:12px;line-height:1.5}
      .dropzone{min-height:150px;border:1px dashed rgba(216,138,59,.35);background:linear-gradient(145deg,rgba(216,138,59,.08),rgba(255,255,255,.015));border-radius:14px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:7px;text-align:center;margin:24px 0 12px;cursor:pointer;transition:border-color .2s,background .2s}
      .dropzone:hover{border-color:rgba(216,138,59,.75);background:linear-gradient(145deg,rgba(216,138,59,.13),rgba(255,255,255,.02))}
      .dropzone input{display:none}
      .dropzone-icon{font-size:28px;line-height:1;color:#d88a3b}
      .geometry-action{width:100%;margin-top:4px}
      .geometry-facts{display:grid;gap:12px;margin-top:28px;padding-top:22px;border-top:1px solid rgba(255,255,255,.08)}
      .geometry-facts div{display:flex;flex-direction:column;gap:4px}
      .geometry-facts span,.triangle-count{font-size:9px;letter-spacing:.12em;color:#7f8994}
      .geometry-facts strong{font-size:13px;font-weight:500}
      .model-panel{padding:18px}
      .model-toolbar{display:flex;align-items:flex-end;justify-content:space-between;padding:4px 4px 14px}
      .model-toolbar h2{margin:0}
      .triangle-count{padding-bottom:3px}
      .viewer-3d{position:relative;overflow:hidden;border:1px solid rgba(255,255,255,.08);border-radius:12px;height:500px;background:#0a0b0d}
      .viewer-3d canvas{display:block}
      .viewer-overlay{position:absolute;left:14px;right:14px;bottom:12px;display:flex;justify-content:space-between;gap:12px;pointer-events:none;font-size:9px;letter-spacing:.1em;color:rgba(255,255,255,.48)}
      .viewer-empty{height:500px;border:1px dashed rgba(255,255,255,.1);border-radius:12px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:9px;text-align:center;background:radial-gradient(circle at 50% 42%,rgba(216,138,59,.08),transparent 38%)}
      .empty-ring{width:72px;height:72px;border:1px solid rgba(216,138,59,.5);border-radius:20px;display:grid;place-items:center;color:#d88a3b;box-shadow:0 0 45px rgba(216,138,59,.12);margin-bottom:5px}
      .provenance-panel{margin-top:20px}
      .provenance-panel h2{margin:0 0 14px}
      @media(max-width:900px){.geometry-grid{grid-template-columns:1fr}.input-panel,.model-panel{min-height:auto}.geometry-heading{flex-direction:column}.viewer-3d,.viewer-empty{height:420px}}
    `}</style>
  </main>;
}
