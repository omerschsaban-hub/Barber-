import { ScrollView, StyleSheet, Text, View } from 'react-native'
import { Card, Header, Screen, StatusPill, Action } from '@/components/ui'
import { theme } from '@/lib/theme'

export default function Overview() {
  return <Screen><ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.content}>
    <Header title="Fabrient" subtitle="Engineering release control, in your pocket." />
    <Card><View style={styles.row}><View><Text style={styles.kicker}>CURRENT RELEASE</Text><Text style={styles.big}>Ready for review</Text></View><StatusPill label="GATED" tone="warning" /></View><Text style={styles.muted}>Geometry and deterministic DFM checks are complete. Physical acceptance remains the final human gate.</Text></Card>
    <View style={styles.grid}>
      <Metric value="12" label="Checks" />
      <Metric value="12/12" label="Passing" />
      <Metric value="0" label="Open risks" />
    </View>
    <Text style={styles.section}>ENGINEERING LOOP</Text>
    {['Define requirements', 'Validate geometry + DFM', 'Verify evidence', 'Release manufacturing package'].map((item, i) => <Card key={item}><View style={styles.row}><Text style={styles.index}>0{i + 1}</Text><Text style={styles.item}>{item}</Text><StatusPill label="PASS" tone="success" /></View></Card>)}
    <View style={styles.actions}><Action title="Open active project" primary /><Action title="Review release record" /></View>
  </ScrollView></Screen>
}
function Metric({ value, label }: { value: string; label: string }) { return <View style={styles.metric}><Text style={styles.metricValue}>{value}</Text><Text style={styles.muted}>{label}</Text></View> }
const styles = StyleSheet.create({ content: { paddingBottom: 30 }, row: { flexDirection: 'row', alignItems: 'center', gap: 10 }, kicker: { color: theme.muted, fontSize: 10, fontWeight: '800', letterSpacing: 1.2 }, big: { color: theme.text, fontSize: 20, fontWeight: '800', marginTop: 4, flex: 1 }, muted: { color: theme.muted, fontSize: 13, lineHeight: 19, marginTop: 12 }, grid: { flexDirection: 'row', gap: 8, marginBottom: 24 }, metric: { flex: 1, backgroundColor: theme.surface, borderWidth: 1, borderColor: theme.border, borderRadius: 14, padding: 14 }, metricValue: { color: theme.text, fontSize: 21, fontWeight: '800' }, section: { color: theme.muted, fontSize: 11, fontWeight: '800', letterSpacing: 1.2, marginBottom: 10 }, index: { color: theme.muted, fontWeight: '800', width: 28 }, item: { color: theme.text, fontWeight: '650', flex: 1 }, actions: { gap: 10, marginTop: 8 } })
