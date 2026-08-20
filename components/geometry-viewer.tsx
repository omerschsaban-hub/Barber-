'use client';
import {useMemo} from 'react';
import * as THREE from 'three';
import {Canvas} from '@react-three/fiber';
import {OrbitControls} from '@react-three/drei';

function Part({size}:{size:number[]}){const material=useMemo(()=>new THREE.MeshStandardMaterial({wireframe:true}),[]);const[x,y,z]=size.map(v=>Math.max(v/20,.1));return <mesh scale={[x,y,z]} material={material}><boxGeometry args={[1,1,1]}/></mesh>}
export default function GeometryViewer({size,deviation}:{size:number[];deviation:number}){return <div className="viewer"><Canvas camera={{position:[3,3,3],fov:45}}><ambientLight intensity={1}/><directionalLight position={[3,4,5]}/><Part size={size}/><OrbitControls/></Canvas><div className="viewer-label">COMPUTED GEOMETRY · DEVIATION {deviation.toFixed(3)} mm</div></div>}
