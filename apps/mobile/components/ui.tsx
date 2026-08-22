import { PropsWithChildren } from 'react'
import { Pressable, StyleSheet, Text, View } from 'react-native'
import { theme, spacing } from '@/lib/theme'

export function Screen({ children }: PropsWithChildren) {
  return <View style={styles.screen}>{children}</View>
}

export function Header({ title, subtitle }: { title: string; subtitle?: string }) {
  return <View style={styles.header}><Text style={styles.title}>{title}</Text>{subtitle ? <Text style={styles.subtitle}>{subtitle}</Text> : null}</View>
}

export function Card({ children }: PropsWithChildren) {
  return <View style={styles.card}>{children}</View>
}

export function StatusPill({ label, tone = 'neutral' }: { label: string; tone?: 'success' | 'warning' | 'danger' | 'neutral' }) {
  const color = tone === 'success' ? theme.success : tone === 'warning' ? theme.warning : tone === 'danger' ? theme.danger : theme.muted
  return <View style={[styles.pill, { borderColor: color + '55' }]}><View style={[styles.dot, { backgroundColor: color }]} /><Text style={[styles.pillText, { color }]}>{label}</Text></View>
}

export function Action({ title, onPress, primary = false }: { title: string; onPress?: () => void; primary?: boolean }) {
  return <Pressable onPress={onPress} style={({ pressed }) => [styles.action, primary && styles.primary, pressed && styles.pressed]}><Text style={[styles.actionText, primary && styles.primaryText]}>{title}</Text></Pressable>
}

export const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.bg, paddingHorizontal: spacing.md, paddingTop: 20 },
  header: { marginBottom: spacing.lg },
  title: { color: theme.text, fontSize: 30, fontWeight: '800', letterSpacing: -0.7 },
  subtitle: { color: theme.muted, fontSize: 14, lineHeight: 20, marginTop: 6 },
  card: { backgroundColor: theme.surface, borderColor: theme.border, borderWidth: 1, borderRadius: 16, padding: spacing.md, marginBottom: spacing.sm },
  pill: { flexDirection: 'row', alignItems: 'center', alignSelf: 'flex-start', borderWidth: 1, borderRadius: 999, paddingHorizontal: 9, paddingVertical: 5, gap: 6 },
  dot: { width: 6, height: 6, borderRadius: 3 },
  pillText: { fontSize: 11, fontWeight: '700' },
  action: { minHeight: 46, borderRadius: 12, borderWidth: 1, borderColor: theme.border, backgroundColor: theme.surface2, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 16 },
  primary: { backgroundColor: theme.text, borderColor: theme.text },
  actionText: { color: theme.text, fontWeight: '700', fontSize: 14 },
  primaryText: { color: theme.bg },
  pressed: { opacity: 0.7 },
})
