import { ImageResponse } from 'next/og'

export const alt = 'Fabrient — From intent to something real'
export const size = { width: 1200, height: 630 }
export const contentType = 'image/png'

export default function Image() {
  return new ImageResponse(
    <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', padding: 72, background: '#f3f0e8', color: '#172019', fontFamily: 'sans-serif' }}>
      <div style={{ fontSize: 28, fontWeight: 800, letterSpacing: 3 }}>FABRIENT / PHYSICAL ENGINEERING</div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
        <div style={{ fontSize: 76, fontWeight: 800, lineHeight: 1.02 }}>From intent<br />to something real.</div>
        <div style={{ fontSize: 30, maxWidth: 920, lineHeight: 1.35 }}>Connect design, engineering, build, measurement, learning and release evidence.</div>
      </div>
      <div style={{ fontSize: 24, fontWeight: 700 }}>Predict → Build → Measure → Learn → Release</div>
    </div>,
    size,
  )
}
