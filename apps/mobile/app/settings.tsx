import { useState } from 'react'
import { Alert, ScrollView, StyleSheet, Text, View } from 'react-native'
import { useRouter } from 'expo-router'
import { Card, Header, Screen, StatusPill, Action } from '@/components/ui'
import { theme } from '@/lib/theme'
import { getCustomerInfo, isPro, presentCustomerCenter, restorePurchases } from '@/lib/revenuecat'

export default function Settings() {
  const router = useRouter()
  const [pro, setPro] = useState(false)

  const refresh = async () => {
    try {
      const info = await getCustomerInfo()
      setPro(isPro(info))
    } catch (error: any) {
      Alert.alert('Subscription status unavailable', error?.message ?? 'Please try again.')
    }
  }

  const manage = async () => {
    if (!pro) {
      router.push('/paywall')
      return
    }
    try {
      await presentCustomerCenter()
      await refresh()
    } catch (error: any) {
      Alert.alert('Subscription management unavailable', error?.message ?? 'Please try again.')
    }
  }

  const restore = async () => {
    try {
      const info = await restorePurchases()
      setPro(isPro(info))
      Alert.alert(isPro(info) ? 'Restored' : 'No active subscription', isPro(info) ? 'Fabrinat Pro is active.' : 'No active Pro subscription was found.')
    } catch (error: any) {
      Alert.alert('Restore failed', error?.message ?? 'Please try again.')
    }
  }

  return <Screen><ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.content}><Header title="Settings" subtitle="Mobile app preferences and connection state." />
    <Card><Text style={styles.label}>SUBSCRIPTION</Text><View style={styles.row}><View style={styles.flex}><Text style={styles.name}>{pro ? 'Fabrinat Pro' : 'Fabrinat Free'}</Text><Text style={styles.detail}>{pro ? 'Advanced engineering features are unlocked.' : 'Core engineering workflow is available for free.'}</Text></View><StatusPill label={pro ? 'PRO' : 'FREE'} tone={pro ? 'success' : 'warning'} /></View><View style={styles.actions}><Action title={pro ? 'Manage subscription' : 'View Pro plans'} primary onPress={() => void manage()} /><Action title="Restore purchases" onPress={() => void restore()} /></View></Card>
    <Card><Text style={styles.label}>BACKEND</Text><View style={styles.row}><Text style={styles.name}>Fabrient services</Text><StatusPill label="CONNECTED" tone="success" /></View><Text style={styles.detail}>The mobile client reuses the existing Fabrient API and Supabase data layer.</Text></Card>
    <Card><Text style={styles.label}>APP</Text>{['Notifications', 'Offline cache', 'Appearance', 'About Fabrient'].map((x, i) => <View key={x} style={[styles.option, i > 0 && styles.border]}><Text style={styles.name}>{x}</Text><Text style={styles.chevron}>›</Text></View>)}</Card>
    <Text style={styles.footer}>Fabrient Mobile · v1.0.0</Text>
  </ScrollView></Screen>
}
const styles = StyleSheet.create({ content: { paddingBottom: 30 }, label: { color: theme.muted, fontSize: 10, fontWeight: '800', letterSpacing: 1.2, marginBottom: 12 }, row: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 12 }, flex: { flex: 1 }, name: { color: theme.text, fontSize: 15, fontWeight: '650' }, detail: { color: theme.muted, fontSize: 12, lineHeight: 18, marginTop: 8 }, option: { minHeight: 48, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }, border: { borderTopWidth: 1, borderTopColor: theme.border }, chevron: { color: theme.muted, fontSize: 24 }, actions: { gap: 10, marginTop: 14 }, footer: { color: theme.muted, textAlign: 'center', fontSize: 11, marginTop: 8 } })
