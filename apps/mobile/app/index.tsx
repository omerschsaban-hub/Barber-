import { useEffect, useState } from 'react'
import { ActivityIndicator, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native'
import { useRouter } from 'expo-router'
import { Action, Card, Header, Screen, StatusPill } from '@/components/ui'
import { theme } from '@/lib/theme'
import { PRODUCT_LOOP } from '@/lib/product-loop'
import { billingAccess, engineeringHealth, type BillingAccess } from '@/lib/api'
import { useAuth } from '@/lib/auth-context'

function SignIn() {
  const { sendOtp, verify, error, clearError } = useAuth()
  const [email, setEmail] = useState('')
  const [code, setCode] = useState('')
  const [step, setStep] = useState<'email' | 'code'>('email')
  const [busy, setBusy] = useState(false)
  const submitEmail = async () => { setBusy(true); clearError(); try { await sendOtp(email); setStep('code') } catch {} finally { setBusy(false) } }
  const submitCode = async () => { setBusy(true); clearError(); try { await verify(email, code) } catch {} finally { setBusy(false) } }
  return <Screen><ScrollView contentContainerStyle={styles.authContent}><Text style={styles.brand}>FABRIENT</Text><Text style={styles.authTitle}>Build with evidence.</Text><Text style={styles.muted}>Sign in to continue to your engineering workspace.</Text><Card><Text style={styles.kicker}>{step === 'email' ? 'EMAIL VERIFICATION' : 'CHECK YOUR INBOX'}</Text>{step === 'email' ? <><TextInput autoCapitalize="none" autoCorrect={false} keyboardType="email-address" placeholder="you@gmail.com" placeholderTextColor={theme.muted} value={email} onChangeText={setEmail} style={styles.input} /><Action title={busy ? 'Sending…' : 'Send code'} primary onPress={busy || !email.trim() ? undefined : submitEmail} /></> : <><Text style={styles.muted}>Enter the six-digit code sent to {email.trim().toLowerCase()}.</Text><TextInput keyboardType="number-pad" maxLength={6} placeholder="000000" placeholderTextColor={theme.muted} value={code} onChangeText={setCode} style={styles.input} /><Action title={busy ? 'Verifying…' : 'Verify and continue'} primary onPress={busy || code.length < 6 ? undefined : submitCode} /><View style={styles.spacer} /><Action title="Use another email" onPress={() => { setStep('email'); setCode('') }} /></>}{error ? <Text style={styles.error}>{error}</Text> : null}</Card></ScrollView></Screen>
}

export default function Overview() {
  const { user, loading } = useAuth()
  const router = useRouter()
  const [billing, setBilling] = useState<BillingAccess | null>(null)
  const [health, setHealth] = useState<'checking' | 'online' | 'offline'>('checking')
  useEffect(() => { if (!user) return; void billingAccess().then(setBilling).catch(() => setBilling(null)); void engineeringHealth().then(() => setHealth('online')).catch(() => setHealth('offline')) }, [user])
  if (loading) return <Screen><ActivityIndicator color={theme.accent} /></Screen>
  if (!user) return <SignIn />
  return <Screen><ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.content}><Header title="Overview" subtitle={`Signed in as ${user.email}`} /><Card><View style={styles.row}><View style={styles.flex}><Text style={styles.kicker}>WORKSPACE STATUS</Text><Text style={styles.big}>Ready for the next decision</Text><Text style={styles.muted}>Run deterministic engineering checks, preserve evidence, and keep every release honest.</Text></View><StatusPill label={health === 'online' ? 'ONLINE' : health === 'offline' ? 'OFFLINE' : 'CHECKING'} tone={health === 'online' ? 'success' : health === 'offline' ? 'danger' : 'warning'} /></View><View style={styles.actions}><Action title="Open projects" primary onPress={() => router.push('/projects')} /></View></Card><Card><View style={styles.row}><View style={styles.flex}><Text style={styles.kicker}>PLAN</Text><Text style={styles.proTitle}>{billing?.plan || 'Free'}</Text><Text style={styles.muted}>{billing?.limits ? 'Usage limits are enforced by the owned backend.' : 'Billing status is loading or unavailable.'}</Text></View><StatusPill label={billing?.pro ? 'ACTIVE' : 'BASIC'} tone={billing?.pro ? 'success' : 'neutral'} /></View><View style={styles.actions}><Action title="View plans" onPress={() => router.push('/paywall')} /></View></Card><Text style={styles.section}>THE PRODUCT LOOP</Text>{PRODUCT_LOOP.map((item, i) => <Card key={item.key}><View style={styles.row}><Text style={styles.index}>0{i + 1}</Text><View style={styles.flex}><Text style={styles.item}>{item.title}</Text><Text style={styles.mutedSmall}>{item.description}</Text></View><StatusPill label={i < 3 ? 'CORE' : 'PRO'} tone={i < 3 ? 'success' : 'warning'} /></View></Card>)}</ScrollView></Screen>
}
const styles = StyleSheet.create({ authContent:{paddingTop:50},brand:{color:theme.accent,fontSize:12,fontWeight:'800',letterSpacing:2},authTitle:{color:theme.text,fontSize:34,fontWeight:'800',marginTop:18},content:{paddingBottom:30},row:{flexDirection:'row',alignItems:'center',gap:10},flex:{flex:1},kicker:{color:theme.muted,fontSize:10,fontWeight:'800',letterSpacing:1.2},big:{color:theme.text,fontSize:22,fontWeight:'800',marginTop:5},proTitle:{color:theme.text,fontSize:18,fontWeight:'800',marginTop:4},muted:{color:theme.muted,fontSize:13,lineHeight:19,marginTop:10},mutedSmall:{color:theme.muted,fontSize:12,lineHeight:17,marginTop:4},section:{color:theme.muted,fontSize:11,fontWeight:'800',letterSpacing:1.2,marginBottom:10},index:{color:theme.muted,fontWeight:'800',width:28},item:{color:theme.text,fontWeight:'700',fontSize:15},actions:{gap:10,marginTop:12},input:{height:48,borderWidth:1,borderColor:theme.border,borderRadius:12,color:theme.text,paddingHorizontal:14,marginVertical:14,fontSize:16},error:{color:theme.danger,fontSize:13,lineHeight:19,marginTop:12},spacer:{height:10}})
