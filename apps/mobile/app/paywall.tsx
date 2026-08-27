import { useCallback, useEffect, useState } from 'react'
import { ActivityIndicator, Alert, ScrollView, StyleSheet, Text, View } from 'react-native'
import { useRouter } from 'expo-router'
import { Action, Card, Header, Screen, StatusPill } from '@/components/ui'
import { theme } from '@/lib/theme'
import {
  getCustomerInfo,
  getCurrentPackages,
  isPro,
  presentFabrinatPaywall,
  restorePurchases,
  type PurchasesPackage,
} from '@/lib/revenuecat'

export default function PaywallScreen() {
  const router = useRouter()
  const [packages, setPackages] = useState<PurchasesPackage[]>([])
  const [pro, setPro] = useState(false)
  const [loading, setLoading] = useState(true)

  const refresh = useCallback(async () => {
    try {
      const [info, available] = await Promise.all([getCustomerInfo(), getCurrentPackages()])
      setPro(isPro(info))
      setPackages(available)
    } catch (error) {
      console.warn('[RevenueCat] Paywall load failed', error)
      Alert.alert('Subscriptions unavailable', 'Please check your connection and try again.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { void refresh() }, [refresh])

  const buy = async (pkg: PurchasesPackage) => {
    try {
      setLoading(true)
      const { purchasePackage } = await import('@/lib/revenuecat')
      const info = await purchasePackage(pkg)
      setPro(isPro(info))
      if (isPro(info)) {
        Alert.alert('Fabrinat Pro is active', 'Your Pro features are unlocked.')
        router.back()
      }
    } catch (error: any) {
      if (!error?.userCancelled) Alert.alert('Purchase failed', error?.message ?? 'Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const restore = async () => {
    try {
      setLoading(true)
      const info = await restorePurchases()
      setPro(isPro(info))
      Alert.alert(isPro(info) ? 'Restored' : 'No active subscription', isPro(info) ? 'Fabrinat Pro is active again.' : 'No Pro entitlement was found.')
      if (isPro(info)) router.back()
    } catch (error: any) {
      Alert.alert('Restore failed', error?.message ?? 'Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const openNativePaywall = async () => {
    try {
      await presentFabrinatPaywall()
      await refresh()
    } catch (error: any) {
      Alert.alert('Paywall unavailable', error?.message ?? 'Please try again.')
    }
  }

  return <Screen><ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.content}>
    <Header title="Fabrinat Pro" subtitle="Unlock the deeper engineering workflow without hiding the basics." />
    <Card>
      <View style={styles.row}><Text style={styles.hero}>Build with more confidence.</Text>{pro && <StatusPill label="ACTIVE" tone="success" />}</View>
      <Text style={styles.muted}>Free stays useful. Pro adds the advanced evidence, exports and tools when you actually need them.</Text>
    </Card>
    <Text style={styles.section}>FREE</Text>
    {['Overview and release status', 'Basic project tracking', 'Deterministic DFM summary'].map(x => <Feature key={x} text={x} />)}
    <Text style={styles.section}>PRO</Text>
    {['Advanced 3D risk analysis', 'Full manufacturing-package export', 'Advanced inspection and analytics', 'Extended MCP tool set'].map(x => <Feature key={x} text={x} premium />)}

    {loading && <ActivityIndicator style={styles.spinner} />}
    {!loading && packages.map(pkg => <Action key={pkg.identifier} title={`${pkg.product.title} · ${pkg.product.priceString}`} primary onPress={() => void buy(pkg)} />)}
    {!loading && packages.length === 0 && <Action title="Open RevenueCat paywall" primary onPress={() => void openNativePaywall()} />}
    <Action title="Restore purchases" onPress={() => void restore()} />
  </ScrollView></Screen>
}

function Feature({ text, premium = false }: { text: string; premium?: boolean }) {
  return <Card><View style={styles.row}><View style={styles.dot}><Text style={styles.dotText}>{premium ? 'P' : '✓'}</Text></View><Text style={styles.feature}>{text}</Text>{premium && <StatusPill label="PRO" tone="warning" />}</View></Card>
}

const styles = StyleSheet.create({
  content: { paddingBottom: 32 },
  row: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  hero: { color: theme.text, fontSize: 21, fontWeight: '800', flex: 1 },
  muted: { color: theme.muted, fontSize: 13, lineHeight: 19, marginTop: 12 },
  section: { color: theme.muted, fontSize: 11, fontWeight: '800', letterSpacing: 1.2, marginVertical: 10 },
  feature: { color: theme.text, fontSize: 14, fontWeight: '700', flex: 1 },
  dot: { width: 28, height: 28, borderRadius: 14, backgroundColor: theme.surface, alignItems: 'center', justifyContent: 'center' },
  dotText: { color: theme.text, fontWeight: '900' },
  spinner: { marginVertical: 16 },
})
