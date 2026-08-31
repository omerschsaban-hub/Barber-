import { useCallback, useEffect, useState } from 'react'
import { Alert, Linking, ScrollView, StyleSheet, Text, View } from 'react-native'
import { Card, Header, Screen, StatusPill, Action } from '@/components/ui'
import { theme } from '@/lib/theme'
import { billingAccess } from '@/lib/api'
import { useRouter } from 'expo-router'

const WEB_BILLING_URL = `${process.env.EXPO_PUBLIC_FABRIENT_WEB_URL || 'https://fabrinat-omega.vercel.app'}/billing`

export default function Settings() {
  const router = useRouter()
  const [plan, setPlan] = useState('free')

  const refresh = useCallback(async () => {
    try { setPlan((await billingAccess()).plan || 'free') }
    catch (error: any) { Alert.alert('Subscription status unavailable', error?.message ?? 'Please try again.') }
  }, [])

  useEffect(() => { void refresh() }, [refresh])

  const manage = async () => {
    if (plan === 'free') { router.push('/paywall'); return }
    await Linking.openURL(WEB_BILLING_URL)
  }

  return <Screen><ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.content}><Header title="Settings" subtitle="Mobile app preferences and connection state." />
    <Card><Text style={styles.label}>SUBSCRIPTION</Text><View style={styles.row}><View style={styles.flex}><Text style={styles.name}>{plan === 'free' ? 'Fabrient Free' : `Fabrient ${plan}`}</Text><Text style={styles.detail}>{plan === 'free' ? 'Core engineering workflow is available for free.' : 'Advanced engineering features are unlocked.'}</Text></View><StatusPill label={plan === 'free' ? 'FREE' : 'ACTIVE'} tone={plan === 'free' ? 'warning' : 'success'} /></View><View style={styles.actions}><Action title={plan === 'free' ? 'View PayPal plans' : 'Manage plan in browser'} primary onPress={() => void manage()} /></View></Card>
    <Card><Text style={styles.label}>BACKEND</Text><View style={styles.row}><Text style={styles.name}>Fabrient services</Text><StatusPill label="CONNECTED" tone="success" /></View><Text style={styles.detail}>The mobile client uses the authenticated Fabrient API; payment secrets remain server-side.</Text></Card>
    <Card><Text style={styles.label}>APP</Text>{['Notifications', 'Offline cache', 'Appearance', 'About Fabrient'].map((x, i) => <View key={x} style={[styles.option, i > 0 && styles.border]}><Text style={styles.name}>{x}</Text><Text style={styles.chevron}>›</Text></View>)}</Card>
    <Text style={styles.footer}>Fabrient Mobile · v1.0.0</Text>
  </ScrollView></Screen>
}
const styles = StyleSheet.create({ content: { paddingBottom: 30 }, label: { color: theme.muted, fontSize: 10, fontWeight: '800', letterSpacing: 1.2, marginBottom: 12 }, row: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 12 }, flex: { flex: 1 }, name: { color: theme.text, fontSize: 15, fontWeight: '700' }, detail: { color: theme.muted, fontSize: 12, lineHeight: 18, marginTop: 8 }, option: { minHeight: 48, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }, border: { borderTopWidth: 1, borderTopColor: theme.border }, chevron: { color: theme.muted, fontSize: 24 }, actions: { gap: 10, marginTop: 14 }, footer: { color: theme.muted, textAlign: 'center', fontSize: 11, marginTop: 8 } })
