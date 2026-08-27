import { NextResponse } from 'next/server'
const MCP=process.env.FABRIENT_MCP_URL
export async function POST(request:Request){
 if(!MCP)return NextResponse.json({error:'MCP OAuth is not configured'},{status:503})
 const body=await request.json().catch(()=>null) as {authorization_id?:string;decision?:string}|null
 if(!body?.authorization_id||!['approve','deny'].includes(body.decision||''))return NextResponse.json({error:'Invalid authorization decision'},{status:400})
 const cookie=request.headers.get('cookie')||''
 const token=cookie.match(/(?:^|;\s*)fabrient_session=([^;]+)/)?.[1]
 if(!token)return NextResponse.json({error:'Unauthorized'},{status:401})
 try{const r=await fetch(`${MCP.replace(/\/$/,'')}/oauth/decide/${encodeURIComponent(body.authorization_id)}/${body.decision}`,{method:'POST',headers:{Authorization:`Bearer ${decodeURIComponent(token)}`},cache:'no-store'});return new NextResponse(await r.text(),{status:r.status,headers:{'content-type':'application/json'}})}catch{return NextResponse.json({error:'MCP OAuth unavailable'},{status:502})}
}
