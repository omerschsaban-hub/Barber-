import { useCallback, useEffect, useState } from 'react'
import { ActivityIndicator, Alert, Linking, ScrollView, StyleSheet, Text, View } from 'react-native'
import { Card, Header, Screen, StatusPill, Action } from '@/components/ui'
import { theme } from '@/lib/theme'
import { billingAccess } from '@/lib/api'

const WEB_BILLING_URL = `${process.env.EXPO_PUBLIC_FABRIENT_WEB_URL || 'https://fabrinat-omega.vercel.app'}/billing`

export default function PaywallScreen() {
  const [pro, setPro] = useState(false)
  const [loading, setLoading] = useState(true)

  const refresh = useCallback(async () => {
    try {
      const access = await billingAccess()
      setPro(access.plan !== 'free')
    } catch (error: any) {
      Alert.alert('Subscription status unavailable', error?.message ?? 'Please try again.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { void refresh() }, [refresh])

  const openWebCheckout = async () => {
    const supported = await Linking.canOpenURL(WEB_BILLING_URL)
    if (!supported) {
      Alert.alert('Checkout unavailable', 'Your device could not open the secure Fabrient web checkout.')
      return
    }
    await Linking.openURL(WEB_BILLING_URL)
  }

  return <Screen><ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.content}>
    <Header title="Fabrient Plans" subtitle="Secure PayPal checkout works from desktop and mobile browsers." />
    <Card><View style={styles.row}><Text style={styles.hero}>Build with more confidence.</Text>{pro && <StatusPill label="ACTIVE" tone="success" />}</View><Text style={styles.muted}>Free stays useful. Paid plans unlock expanded engineering tools after the backend verifies the PayPal subscription webhook.</Text></Card>
    <Text style={styles.section}>FREE</Text>
    {['Overview and release status', 'Basic project tracking', 'Deterministic DFM summary'].map(x => <Feature key={x} text={x} />)}
    <Text style={styles.section}>PAID PLANS</Text>
    {['Hobby · $9/month', 'Startup · $49/month', 'Secure PayPal web checkout', 'Backend-verified entitlement access'].map(x => <Feature key={x} text={x} premium />)}
    {loading && <ActivityIndicator style={styles.spinner} />}
    {!loading && <Action title={pro ? 'Manage plan in browser' : 'Open secure PayPal checkout'} primary onPress={() => void openWebCheckout()} />}
  </ScrollView></Screen>
}

function Feature({ text, premium = false }: { text: string; premium?: boolean }) {
  return <Card><View style={styles.row}><View style={styles.dot}><Text style={styles.dotText}>{premium ? 'P' : '✓'}</Text></View><Text style={styles.feature}>{text}</Text>{premium && <StatusPill label="PAID" tone="warning" />}</View></Card>
}

const styles = StyleSheet.create({ content: { paddingBottom: 32 }, row: { flexDirection: 'row', alignItems: 'center', gap: 10 }, hero: { color: theme.text, fontSize: 21, fontWeight: '800', flex: 1 }, muted: { color: theme.muted, fontSize: 13, lineHeight: 19, marginTop: 12 }, section: { color: theme.muted, fontSize: 11, fontWeight: '800', letterSpacing: 1.2, marginVertical: 10 }, feature: { color: theme.text, fontSize: 14, fontWeight: '700', flex: 1 }, dot: { width: 28, height: 28, borderRadius: 14, backgroundColor: theme.surface, alignItems: 'center', justifyContent: 'center' }, dotText: { color: theme.text, fontWeight: '900' }, spinner: { marginVertical: 16 } })
