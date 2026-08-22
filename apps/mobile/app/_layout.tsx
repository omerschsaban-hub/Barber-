import { Tabs } from 'expo-router'
import { StatusBar } from 'expo-status-bar'

export default function RootLayout() {
  return (
    <>
      <StatusBar style="light" />
      <Tabs screenOptions={{ headerShown: false, tabBarActiveTintColor: '#ffffff', tabBarInactiveTintColor: '#718096', tabBarStyle: { backgroundColor: '#0b0f14', borderTopColor: '#202832', height: 64, paddingBottom: 8, paddingTop: 7 }, tabBarLabelStyle: { fontSize: 11, fontWeight: '600' } }}>
        <Tabs.Screen name="index" options={{ title: 'Overview' }} />
        <Tabs.Screen name="projects" options={{ title: 'Projects' }} />
        <Tabs.Screen name="release" options={{ title: 'Release' }} />
        <Tabs.Screen name="settings" options={{ title: 'Settings' }} />
      </Tabs>
    </>
  )
}
