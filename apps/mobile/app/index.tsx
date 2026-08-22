import { useEffect, useState } from 'react'
import { ScrollView, StyleSheet, Text, View } from 'react-native'
import { useRouter } from 'expo-router'
import { Card, Header, Screen, StatusPill, Action } from '@/components/ui'
import { theme } from '@/lib/theme'
import { getCustomerInfo, isPro, subscribeToCustomerInfo } from '@/lib/revenuecat'
import { PRODUCT_LOOP } from '@/lib/product-loop'

export default function Overview() {
  const router = useRouter(); const [pro, setPro] = useState(false)
  useEffect(() => { void getCustomerInfo().then(i => setPro(isPro(i))).catch(() => undefined); return subscribeToCustomerInfo(i => setPro(isPro(i))) }, [])
  return <Screen><ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.content}>
    <Header title="Fabrinat" subtitle="From idea to real product." />
    <Card><Text style={styles.kicker}>YOUR NEXT STEP</Text><Text style={styles.big}>Check the active design</Text><Text style={styles.muted}>Fabrinat finds problems, keeps the evidence, prepares the build and learns from what happens in the real world.</Text><View style={styles.actions}><Action title="Open project" primary /></View></Card>
    <Text style={styles.section}>THE PRODUCT LOOP</Text>
    {PRODUCT_LOOP.map((item, i) => <Card key={item.key}><View style={styles.row}><Text style={styles.index}>0{i + 1}</Text><View style={styles.flex}><Text style={styles.item}>{item.title}</Text><Text style={styles.mutedSmall}>{item.description}</Text></View><StatusPill label={i < 3 ? 'CORE' : 'PRO'} tone={i < 3 ? 'success' : 'warning'} /></View></Card>)}
    <Card><View style={styles.row}><View style={styles.flex}><Text style={styles.kicker}>HOBBYIST</Text><Text style={styles.proTitle}>{pro ? 'Advanced workflow active' : 'Build the full loop'}</Text><Text style={styles.muted}>{pro ? 'Fixes, build packages, automation, simulation and production feedback are available.' : 'Unlock the tools that take you from a good design to a repeatable physical product.'}</Text></View>{!pro && <StatusPill label="PRO" tone="warning" />}</View>{!pro && <View style={styles.actions}><Action title="See plans" primary onPress={() => router.push('/paywall')} /></View>}</Card>
  </ScrollView></Screen>
}
const styles = StyleSheet.create({content:{paddingBottom:30},row:{flexDirection:'row',alignItems:'center',gap:10},flex:{flex:1},kicker:{color:theme.muted,fontSize:10,fontWeight:'800',letterSpacing:1.2},big:{color:theme.text,fontSize:22,fontWeight:'800',marginTop:5},proTitle:{color:theme.text,fontSize:18,fontWeight:'800',marginTop:4},muted:{color:theme.muted,fontSize:13,lineHeight:19,marginTop:10},mutedSmall:{color:theme.muted,fontSize:12,lineHeight:17,marginTop:4},section:{color:theme.muted,fontSize:11,fontWeight:'800',letterSpacing:1.2,marginBottom:10},index:{color:theme.muted,fontWeight:'800',width:28},item:{color:theme.text,fontWeight:'700',fontSize:15},actions:{gap:10,marginTop:12}})
