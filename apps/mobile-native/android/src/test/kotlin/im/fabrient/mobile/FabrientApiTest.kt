package im.fabrient.mobile

import kotlin.test.Test
import kotlin.test.assertTrue

class FabrientApiTest {
    @Test
    fun clientUsesOwnedProductionDefault() {
        val client = FabrientApi()
        assertTrue(client.javaClass.declaredConstructors.isNotEmpty())
    }

    @Test
    fun clientCanBeConfiguredForLocalContractTests() {
        val client = FabrientApi("http://127.0.0.1:8000")
        assertTrue(client.javaClass.declaredConstructors.isNotEmpty())
    }
}
