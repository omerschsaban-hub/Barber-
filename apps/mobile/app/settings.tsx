import { ScrollView, StyleSheet, Text, View } from 'react-native'
import { Card, Header, Screen, StatusPill } from '@/components/ui'
import { theme } from '@/lib/theme'

export default function Settings() {
  return <Screen><ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.content}><Header title="Settings" subtitle="Mobile app preferences and connection state." />
    <Card><Text style={styles.label}>BACKEND</Text><View style={styles.row}><Text style={styles.name}>Fabrient services</Text><StatusPill label="CONNECTED" tone="success" /></View><Text style={styles.detail}>The mobile client is designed to reuse the existing Fabrient API and Supabase data layer.</Text></Card>
    <Card><Text style={styles.label}>APP</Text>{['Notifications', 'Offline cache', 'Appearance', 'About Fabrient'].map((x, i) => <View key={x} style={[styles.option, i > 0 && styles.border]}><Text style={styles.name}>{x}</Text><Text style={styles.chevron}>›</Text></View>)}</Card>
    <Text style={styles.footer}>Fabrient Mobile · v1.0.0</Text>
  </ScrollView></Screen>
}
const styles = StyleSheet.create({ content: { paddingBottom: 30 }, label: { color: theme.muted, fontSize: 10, fontWeight: '800', letterSpacing: 1.2, marginBottom: 12 }, row: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }, name: { color: theme.text, fontSize: 15, fontWeight: '650' }, detail: { color: theme.muted, fontSize: 12, lineHeight: 18, marginTop: 10 }, option: { minHeight: 48, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }, border: { borderTopWidth: 1, borderTopColor: theme.border }, chevron: { color: theme.muted, fontSize: 24 }, footer: { color: theme.muted, textAlign: 'center', fontSize: 11, marginTop: 8 } })
