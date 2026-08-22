'use client'

import Purchases, { type CustomerInfo, type PurchasesOffering, type PurchasesPackage } from '@revenuecat/purchases-js'

export const FABRINAT_PRO_ENTITLEMENT = 'create_an_app_called_fabrinat_pro'

let purchases: Purchases | null = null

export function configureRevenueCatWeb(appUserId: string) {
  if (purchases) return purchases
  const apiKey = process.env.NEXT_PUBLIC_REVENUECAT_WEB_API_KEY
  if (!apiKey) throw new Error('RevenueCat web billing is not configured')
  purchases = Purchases.configure({ apiKey, appUserId })
  return purchases
}

export async function getWebOffering(appUserId: string): Promise<PurchasesOffering | null> {
  const client = configureRevenueCatWeb(appUserId)
  const offerings = await client.getOfferings()
  return offerings.current ?? null
}

export async function purchaseWebPackage(appUserId: string, pkg: PurchasesPackage) {
  const client = configureRevenueCatWeb(appUserId)
  return client.purchase({ rcPackage: pkg })
}

export async function getWebCustomerInfo(appUserId: string): Promise<CustomerInfo> {
  const client = configureRevenueCatWeb(appUserId)
  return client.getCustomerInfo()
}

export function hasProEntitlement(info: CustomerInfo | null | undefined) {
  return Boolean(info?.entitlements.active[FABRINAT_PRO_ENTITLEMENT])
}
