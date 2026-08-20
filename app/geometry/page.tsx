'use client';

import {useMemo, useState} from 'react';
import {Canvas} from '@react-three/fiber';
import {OrbitControls} from '@react-three/drei';
import * as THREE from 'three';

const ENGINE = process.env.NEXT_PUBLIC_ENGINEERING_API || process.env.NEXT_PUBLIC_ENGINEERING_URL || 'http://localhost:8000';

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
  const geometry = useMemo(() => {
    const g = new THREE.BufferGeometry();
    const positions = new Float32Array(mesh.vertices.flatMap(v => [v[0], v[1], v[2]]));
    const indices = new Uint32Array(mesh.triangles.flatMap(t => [t[0], t[1], t[2]]));
    g.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    g.setIndex(new THREE.BufferAttribute(indices, 1));
    g.computeVertexNormals();
    g.computeBoundingSphere();
    return g;
  }, [mesh]);

  return <mesh geometry={geometry}><meshStandardMaterial metalness={0.15} roughness={0.65} side={THREE.DoubleSide}/></mesh>;
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

  return <main className="page wide">
    <div className="eyebrow">GEOMETRY / STEP</div>
    <h1 className="title">Kernel-verified 3D geometry</h1>
    <p className="muted">Upload a STEP file. Fabrient extracts verified BREP topology and a deterministic OCCT tessellation; the browser renders that kernel-derived mesh rather than a guessed bounding-box primitive.</p>
    <div className="workspace-grid">
      <section className="panel">
        <h2>STEP INPUT</h2>
        <input type="file" accept=".step,.stp" onChange={e=>setFile(e.target.files?.[0])}/>
        <button className="button primary" disabled={!file||loading} onClick={run}>{loading?'Extracting…':'Extract & visualize'}</button>
        {error&&<p className="error" role="alert">{error}</p>}
        {data&&<>
          <p><strong>Status:</strong> {data.status}</p>
          <p><strong>Topology:</strong> {data.brep?.solids ?? 0} solids · {data.brep?.faces ?? 0} faces · {data.brep?.edges ?? 0} edges</p>
          <p className="muted">Topology verified: {String(data.provenance?.topology_verified??false)}</p>
          <pre className="provenance">{JSON.stringify(data.provenance,null,2)}</pre>
        </>}
      </section>
      <section className="panel">
        <h2>3D MODEL VIEW</h2>
        {size?.length===3&&mesh?<div className="viewer">
          <Canvas camera={{position:[2,2,2]}}>
            <ambientLight intensity={0.8}/><directionalLight position={[3,4,5]} intensity={2}/>
            <KernelMesh mesh={mesh}/><OrbitControls enableDamping/>
          </Canvas>
          <div className="viewer-label">{size.map((v:number)=>v.toFixed(3)).join(' × ')} {data.bounding_box.units} · {mesh.triangle_count ?? mesh.triangles.length} triangles</div>
        </div>:<p className="muted">No verified STEP mesh has been extracted yet.</p>}
      </section>
    </div>
  </main>;
}
