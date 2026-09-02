import { ImageResponse } from 'next/og'

export const alt = 'Fabrient — From intent to something real'
export const size = { width: 1200, height: 630 }
export const contentType = 'image/png'

export default function Image() {
  return new ImageResponse(
    <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center', padding: 72, background: '#f3f0e8', color: '#172019', fontFamily: 'sans-serif' }}>
      <div style={{ fontSize: 28, fontWeight: 800, letterSpacing: 3 }}>FABRIENT</div>
      <div style={{ display: 'flex', flexDirection: 'column', fontSize: 76, fontWeight: 800, lineHeight: 1.02, marginTop: 28 }}><span>From intent</span><span>to something real.</span></div>
      <div style={{ fontSize: 28, marginTop: 28 }}>Physical engineering from design to proof.</div>
    </div>,
    size,
  )
}
