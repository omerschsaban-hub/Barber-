'use client'

import { Purchases } from '@revenuecat/purchases-js'

export const FABRINAT_PRO_ENTITLEMENT = 'create_an_app_called_fabrinat_pro'

let purchases: any = null
let configuredUserId: string | null = null

export async function configureRevenueCatWeb(appUserId: string) {
  if (!appUserId) throw new Error('RevenueCat customer identity is required')
  const apiKey = process.env.NEXT_PUBLIC_REVENUECAT_WEB_API_KEY
  if (!apiKey) throw new Error('RevenueCat web billing is not configured')
  if (!purchases) {
    purchases = Purchases.configure({ apiKey, appUserId })
    configuredUserId = appUserId
  } else if (configuredUserId !== appUserId) {
    await purchases.identifyUser(appUserId)
    configuredUserId = appUserId
  }
  return purchases
}

export async function getWebOffering(appUserId: string) {
  const client = await configureRevenueCatWeb(appUserId)
  const offerings = await client.getOfferings()
  return offerings.current ?? null
}

export async function purchaseWebPackage(appUserId: string, pkg: any) {
  const client = await configureRevenueCatWeb(appUserId)
  return client.purchase({ rcPackage: pkg })
}

export async function getWebCustomerInfo(appUserId: string) {
  const client = await configureRevenueCatWeb(appUserId)
  return client.getCustomerInfo()
}

export function hasProEntitlement(info: any) {
  return Boolean(info?.entitlements?.active?.[FABRINAT_PRO_ENTITLEMENT])
}
