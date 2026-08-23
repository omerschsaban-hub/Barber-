'use client'

export default function GlobalError({reset}:{error:Error & {digest?:string};reset:()=>void}){
  return <html lang="en"><body><main style={{minHeight:'100vh',display:'grid',placeItems:'center',padding:32,fontFamily:'system-ui'}}><section style={{maxWidth:720}}><div style={{fontSize:12,letterSpacing:2,opacity:.65}}>FABRIENT / RECOVERY</div><h1>Fabrient could not render this page.</h1><p>The application encountered a client/runtime failure instead of silently showing a blank page.</p><button onClick={()=>reset()} style={{padding:'10px 16px',cursor:'pointer'}}>Reload workspace</button></section></main></body></html>
}
