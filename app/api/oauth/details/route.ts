import { NextResponse } from 'next/server'
const MCP=process.env.FABRIENT_MCP_URL
export async function GET(request:Request){
 if(!MCP)return NextResponse.json({error:'MCP OAuth is not configured'},{status:503})
 const id=new URL(request.url).searchParams.get('authorization_id')
 if(!id)return NextResponse.json({error:'Missing authorization request'},{status:400})
 try{const r=await fetch(`${MCP.replace(/\/$/,'')}/oauth/details/${encodeURIComponent(id)}`,{cache:'no-store'});return new NextResponse(await r.text(),{status:r.status,headers:{'content-type':'application/json'}})}catch{return NextResponse.json({error:'MCP OAuth unavailable'},{status:502})}
}
