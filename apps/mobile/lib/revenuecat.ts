import { Platform } from 'react-native'
import Purchases, { LOG_LEVEL, type CustomerInfo, type PurchasesPackage } from 'react-native-purchases'
import RevenueCatUI from 'react-native-purchases-ui'
import { supabase } from './supabase'

export const FABRINAT_PRO_ENTITLEMENT = 'create_an_app_called_fabrinat_pro'
export const REVENUECAT_API_KEY = 'test_NxIETMKVJqdYpjlVDuWZtwIQtjT'

let configured = false

export async function configureRevenueCat() {
  if (configured || Platform.OS === 'web') return

  Purchases.setLogLevel(__DEV__ ? LOG_LEVEL.DEBUG : LOG_LEVEL.ERROR)
  Purchases.configure({ apiKey: REVENUECAT_API_KEY })
  configured = true

  try {
    const { data } = await supabase?.auth.getUser() ?? { data: { user: null } }
    if (data.user) {
      await Purchases.logIn(data.user.id)
    }
  } catch (error) {
    console.warn('[RevenueCat] Could not sync authenticated user', error)
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
  return RevenueCatUI.presentPaywall({
    requiredEntitlementIdentifier: FABRINAT_PRO_ENTITLEMENT,
  })
}

export async function presentCustomerCenter() {
  await configureRevenueCat()
  return RevenueCatUI.presentCustomerCenter()
}

export function subscribeToCustomerInfo(listener: (info: CustomerInfo) => void) {
  if (!configured || Platform.OS === 'web') return () => undefined
  return Purchases.addCustomerInfoUpdateListener(listener)
}
