import { ScrollView, StyleSheet, Text, View } from 'react-native'
import { Card, Header, Screen, StatusPill, Action } from '@/components/ui'
import { theme } from '@/lib/theme'

const gates: [string, string, string, 'success' | 'warning' | 'danger' | 'neutral'][] = [
  ['Geometry', 'Deterministic dimensions and topology', 'PASS', 'success' as const],
  ['DFM', 'Manufacturability rules and constraints', 'PASS', 'success' as const],
  ['Verification', 'Simulation and physical evidence', 'REVIEW', 'warning' as const],
  ['Manufacturing', 'Package is gated by acceptance', 'LOCKED', 'neutral' as const],
]

export default function Release() {
  return <Screen><ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.content}><Header title="Release" subtitle="A release is only as strong as its evidence." />
    <Card><Text style={styles.kicker}>RELEASE CANDIDATE</Text><Text style={styles.name}>iPhone Enclosure · Rev 04</Text><View style={styles.score}><Text style={styles.scoreValue}>3 / 4</Text><StatusPill label="HUMAN REVIEW" tone="warning" /></View></Card>
    {gates.map(([name, detail, status, tone]) => <Card key={name}><View style={styles.row}><View style={styles.copy}><Text style={styles.gate}>{name}</Text><Text style={styles.detail}>{detail}</Text></View><StatusPill label={status} tone={tone} /></View></Card>)}
    <Action title="Review evidence" primary /><View style={{ height: 10 }} /><Action title="Open manufacturing package" />
  </ScrollView></Screen>
}
const styles = StyleSheet.create({ content: { paddingBottom: 30 }, kicker: { color: theme.muted, fontSize: 10, fontWeight: '800', letterSpacing: 1.2 }, name: { color: theme.text, fontSize: 19, fontWeight: '800', marginTop: 6 }, score: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginTop: 18 }, scoreValue: { color: theme.text, fontSize: 28, fontWeight: '800' }, row: { flexDirection: 'row', alignItems: 'center', gap: 12 }, copy: { flex: 1 }, gate: { color: theme.text, fontSize: 15, fontWeight: '700' }, detail: { color: theme.muted, fontSize: 12, lineHeight: 18, marginTop: 4 } })
