import { ScrollView, StyleSheet, Text, View } from 'react-native'
import { Card, Header, Screen, StatusPill, Action } from '@/components/ui'
import { theme } from '@/lib/theme'

const projects = [
  { name: 'iPhone Enclosure', meta: 'Rev 04 · Updated today', status: 'In verification', tone: 'warning' as const },
  { name: 'Robotics Controller Case', meta: 'Rev 02 · Updated yesterday', status: 'Released', tone: 'success' as const },
]

export default function Projects() {
  return <Screen><ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.content}><Header title="Projects" subtitle="Your engineering records and release state." />
    <Action title="＋  Start a new build" primary />
    <View style={{ height: 16 }} />
    {projects.map(p => <Card key={p.name}><View style={styles.row}><View style={styles.copy}><Text style={styles.name}>{p.name}</Text><Text style={styles.meta}>{p.meta}</Text></View><StatusPill label={p.status} tone={p.tone} /></View><View style={styles.divider} /><View style={styles.row}><Text style={styles.small}>Geometry ✓   DFM ✓   Evidence {p.tone === 'success' ? '✓' : '…'}</Text><Text style={styles.open}>Open ›</Text></View></Card>)}
  </ScrollView></Screen>
}
const styles = StyleSheet.create({ content: { paddingBottom: 30 }, row: { flexDirection: 'row', alignItems: 'center', gap: 10 }, copy: { flex: 1 }, name: { color: theme.text, fontSize: 17, fontWeight: '750' }, meta: { color: theme.muted, fontSize: 12, marginTop: 5 }, divider: { height: 1, backgroundColor: theme.border, marginVertical: 14 }, small: { color: theme.muted, fontSize: 12, flex: 1 }, open: { color: theme.text, fontSize: 12, fontWeight: '700' } })
