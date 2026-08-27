import { Platform } from 'react-native'
import Purchases, { LOG_LEVEL, type CustomerInfo, type PurchasesPackage } from 'react-native-purchases'
import RevenueCatUI from 'react-native-purchases-ui'
import { currentUser } from './api'

export type { PurchasesPackage }

export const FABRINAT_PRO_ENTITLEMENT = 'create_an_app_called_fabrinat_pro'
const configuredApiKey = process.env.EXPO_PUBLIC_REVENUECAT_API_KEY

let configured = false
let loggedInUserId: string | null = null

async function syncRevenueCatUser() {
  if (!configured || Platform.OS === 'web') return
  let userId: string | null = null
  try { userId = (await currentUser()).user.id } catch { return }
  if (!userId || userId === loggedInUserId) return
  await Purchases.logIn(userId)
  loggedInUserId = userId
}

export async function configureRevenueCat() {
  if (Platform.OS === 'web') return
  if (!configured) {
    if (!configuredApiKey) throw new Error('RevenueCat mobile billing is not configured')
    Purchases.setLogLevel(__DEV__ ? LOG_LEVEL.DEBUG : LOG_LEVEL.ERROR)
    Purchases.configure({ apiKey: configuredApiKey })
    configured = true
  }
  try {
    await syncRevenueCatUser()
  } catch (error) {
    console.warn('[RevenueCat] Could not sync authenticated user', error)
  }
}

export async function syncRevenueCatAuth() {
  await configureRevenueCat()
  try {
    await syncRevenueCatUser()
  } catch (error) {
    console.warn('[RevenueCat] Could not sync auth state', error)
  }
}

export function isPro(customerInfo: CustomerInfo | null | undefined) {
  return Boolean(customerInfo?.entitlements.active[FABRINAT_PRO_ENTITLEMENT])
}

export async function getCustomerInfo() {
  await configureRevenueCat()
  return Purchases.getCustomerInfo()
}

export async function getCurrentPackages(): Promise<PurchasesPackage[]> {
  await configureRevenueCat()
  const offerings = await Purchases.getOfferings()
  return offerings.current?.availablePackages ?? []
}

export async function purchasePackage(pkg: PurchasesPackage) {
  await configureRevenueCat()
  const result = await Purchases.purchasePackage(pkg)
  return result.customerInfo
}

export async function restorePurchases() {
  await configureRevenueCat()
  return Purchases.restorePurchases()
}

export async function presentFabrinatPaywall() {
  await configureRevenueCat()
  return RevenueCatUI.presentPaywallIfNeeded({
    requiredEntitlementIdentifier: FABRINAT_PRO_ENTITLEMENT,
  })
}

export async function presentCustomerCenter() {
  await configureRevenueCat()
  return RevenueCatUI.presentCustomerCenter()
}

export function subscribeToCustomerInfo(listener: (info: CustomerInfo) => void) {
  if (!configured || Platform.OS === 'web') return
  void Purchases.addCustomerInfoUpdateListener(listener)
}
