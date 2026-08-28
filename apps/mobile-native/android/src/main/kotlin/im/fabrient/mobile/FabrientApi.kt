package im.fabrient.mobile

import java.net.HttpURLConnection
import java.net.URI
import java.net.http.HttpClient
import java.net.http.HttpRequest
import java.net.http.HttpResponse
import java.time.Duration

/** Minimal Android/JVM client for the owned Fabrient API. Tokens stay in the caller's secure storage. */
class FabrientApi(
    private val baseUrl: String = "https://fabrient-engineering.onrender.com",
    private val http: HttpClient = HttpClient.newBuilder()
        .connectTimeout(Duration.ofSeconds(10))
        .build(),
) {
    data class User(val id: String, val email: String, val displayName: String? = null)
    data class AuthResult(val user: User, val sessionToken: String, val expiresIn: Long)
    data class BillingAccess(val authenticated: Boolean, val pro: Boolean, val plan: String)
    data class Health(val ok: Boolean, val service: String, val databaseConfigured: Boolean?)

    fun requestOtp(email: String): String = post("/auth/request-otp", "{\"email\":\"${json(email.trim().lowercase())}\"}")

    fun verifyOtp(email: String, code: String): String = post(
        "/auth/verify-otp",
        "{\"email\":\"${json(email.trim().lowercase())}\",\"code\":\"${json(code.trim())}\"}",
    )

    fun currentUser(token: String): String = get("/auth/me", token)

    fun billingAccess(token: String): String = get("/billing/access", token)

    fun health(): String = get("/health", null)

    fun logout(token: String): String = post("/auth/logout", "{}", token)

    private fun get(path: String, token: String?): String {
        val builder = HttpRequest.newBuilder(URI.create(baseUrl.trimEnd('/') + path))
            .timeout(Duration.ofSeconds(20))
            .header("Accept", "application/json")
        if (!token.isNullOrBlank()) builder.header("Authorization", "Bearer $token")
        return send(builder.GET().build())
    }

    private fun post(path: String, body: String, token: String? = null): String {
        val builder = HttpRequest.newBuilder(URI.create(baseUrl.trimEnd('/') + path))
            .timeout(Duration.ofSeconds(20))
            .header("Accept", "application/json")
            .header("Content-Type", "application/json")
            .POST(HttpRequest.BodyPublishers.ofString(body))
        if (!token.isNullOrBlank()) builder.header("Authorization", "Bearer $token")
        return send(builder.build())
    }

    private fun send(request: HttpRequest): String {
        val response = http.send(request, HttpResponse.BodyHandlers.ofString())
        if (response.statusCode() !in 200..299) {
            throw IllegalStateException("Fabrient request failed (${response.statusCode()})")
        }
        return response.body()
    }

    private fun json(value: String): String = value
        .replace("\\", "\\\\")
        .replace("\"", "\\\"")
        .replace("\n", "\\n")
}
