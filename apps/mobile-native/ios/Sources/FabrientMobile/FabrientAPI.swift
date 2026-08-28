import Foundation

public struct FabrientAPI {
    public struct User: Codable, Equatable {
        public let id: String
        public let email: String
        public let displayName: String?

        enum CodingKeys: String, CodingKey {
            case id
            case email
            case displayName = "display_name"
        }
    }

    public struct AuthResult: Codable, Equatable {
        public let user: User
        public let sessionToken: String
        public let expiresIn: Int

        enum CodingKeys: String, CodingKey {
            case user
            case sessionToken = "session_token"
            case expiresIn = "expires_in"
        }
    }

    public struct BillingAccess: Codable, Equatable {
        public let authenticated: Bool
        public let pro: Bool
        public let plan: String
    }

    public struct Health: Codable, Equatable {
        public let ok: Bool
        public let service: String
        public let databaseConfigured: Bool?

        enum CodingKeys: String, CodingKey {
            case ok
            case service
            case databaseConfigured = "database_configured"
        }
    }

    public enum APIError: Error, Equatable {
        case invalidResponse
        case server(status: Int)
    }

    public var baseURL: URL
    public var session: URLSession

    public init(baseURL: URL = URL(string: "https://fabrient-engineering.onrender.com")!, session: URLSession = .shared) {
        self.baseURL = baseURL
        self.session = session
    }

    public func requestOTP(email: String) async throws {
        _ = try await request(path: "/auth/request-otp", method: "POST", body: ["email": email.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()])
    }

    public func verifyOTP(email: String, code: String) async throws -> AuthResult {
        let data = try await request(path: "/auth/verify-otp", method: "POST", body: ["email": email.lowercased(), "code": code])
        return try JSONDecoder().decode(AuthResult.self, from: data)
    }

    public func currentUser(token: String) async throws -> User {
        let data = try await request(path: "/auth/me", token: token)
        return try JSONDecoder().decode(User.self, from: data)
    }

    public func billingAccess(token: String) async throws -> BillingAccess {
        let data = try await request(path: "/billing/access", token: token)
        return try JSONDecoder().decode(BillingAccess.self, from: data)
    }

    public func health() async throws -> Health {
        let data = try await request(path: "/health")
        return try JSONDecoder().decode(Health.self, from: data)
    }

    public func logout(token: String) async throws {
        _ = try await request(path: "/auth/logout", method: "POST", token: token, body: [:])
    }

    private func request(path: String, method: String = "GET", token: String? = nil, body: [String: String]? = nil) async throws -> Data {
        var request = URLRequest(url: baseURL.appendingPathComponent(path.trimmingCharacters(in: CharacterSet(charactersIn: "/"))))
        request.httpMethod = method
        request.timeoutInterval = 20
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        if body != nil {
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
            request.httpBody = try JSONSerialization.data(withJSONObject: body ?? [:])
        }
        if let token, !token.isEmpty { request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization") }
        let (data, response) = try await session.data(for: request)
        guard let http = response as? HTTPURLResponse else { throw APIError.invalidResponse }
        guard (200..<300).contains(http.statusCode) else { throw APIError.server(status: http.statusCode) }
        return data
    }
}
