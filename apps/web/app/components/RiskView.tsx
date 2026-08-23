'use client'
import {useEffect,useRef,useState} from 'react'
import * as THREE from 'three'

export default function RiskView({size=[40,20,10],risk=0}:{size?:number[];risk?:number}){
  const ref=useRef<HTMLDivElement>(null)
  const [failed,setFailed]=useState(false)

  useEffect(()=>{
    if(!ref.current)return
    const el=ref.current
    let renderer: THREE.WebGLRenderer | null=null
    let geom: THREE.BoxGeometry | null=null
    let mat: THREE.MeshStandardMaterial | null=null
    let raf=0

    try{
      if(!('WebGLRenderingContext' in window)) throw new Error('WebGL is unavailable')
      const scene=new THREE.Scene()
      scene.background=new THREE.Color(0x090908)
      const camera=new THREE.PerspectiveCamera(45,1,.1,1000)
      camera.position.set(55,45,55)
      camera.lookAt(0,0,0)
      renderer=new THREE.WebGLRenderer({antialias:true})
      renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,2))
      renderer.setSize(Math.max(el.clientWidth,320),320)
      el.appendChild(renderer.domElement)

      geom=new THREE.BoxGeometry(size[0],size[1],size[2])
      mat=new THREE.MeshStandardMaterial({color:risk>=1?0xb53a32:risk>=.5?0xd9b33b:0x7aa66d,roughness:.75})
      const mesh=new THREE.Mesh(geom,mat)
      scene.add(mesh)
      const edgesGeom=new THREE.EdgesGeometry(geom)
      const edges=new THREE.LineSegments(edgesGeom,new THREE.LineBasicMaterial({color:0xe9e7df}))
      scene.add(edges)
      scene.add(new THREE.AmbientLight(0xffffff,.7))
      const light=new THREE.DirectionalLight(0xffffff,1.1)
      light.position.set(30,40,50)
      scene.add(light)

      const loop=()=>{
        if(!renderer)return
        mesh.rotation.y+=.003
        edges.rotation.y=mesh.rotation.y
        renderer.render(scene,camera)
        raf=requestAnimationFrame(loop)
      }
      loop()

      const ro=new ResizeObserver(()=>{
        if(!ref.current||!renderer)return
        const width=Math.max(ref.current.clientWidth,320)
        renderer.setSize(width,320)
        camera.aspect=width/320
        camera.updateProjectionMatrix()
      })
      ro.observe(el)

      return()=>{
        cancelAnimationFrame(raf)
        ro.disconnect()
        renderer?.dispose()
        geom?.dispose()
        mat?.dispose()
        edgesGeom.dispose()
        if(renderer?.domElement.parentNode===el)el.removeChild(renderer.domElement)
      }
    }catch{
      setFailed(true)
      renderer?.dispose()
      if(renderer?.domElement.parentNode===el)el.removeChild(renderer.domElement)
    }
  },[size.join(','),risk])

  if(failed)return <div role="status" style={{width:'100%',minHeight:320,display:'grid',placeItems:'center',border:'1px solid rgba(255,255,255,.12)',padding:24}}><div><strong>3D preview unavailable</strong><p style={{opacity:.7}}>The engineering workspace is still available; this device cannot initialize WebGL.</p></div></div>
  return <div ref={ref} aria-label="Computed 3D engineering risk visualization" style={{width:'100%',minHeight:320}}/>
}
