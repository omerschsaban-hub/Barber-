import XCTest
@testable import FabrientMobile

final class FabrientAPITests: XCTestCase {
    func testAuthResultDecodesOwnedSnakeCaseFields() throws {
        let data = Data(#"{"user":{"id":"u1","email":"user@example.com","display_name":"User"},"session_token":"redacted-test-token","expires_in":3600}"#.utf8)
        let result = try JSONDecoder().decode(FabrientAPI.AuthResult.self, from: data)
        XCTAssertEqual(result.user.id, "u1")
        XCTAssertEqual(result.user.email, "user@example.com")
        XCTAssertEqual(result.sessionToken, "redacted-test-token")
        XCTAssertEqual(result.expiresIn, 3600)
    }

    func testHealthDecodesDatabaseFlag() throws {
        let data = Data(#"{"ok":true,"service":"fabrient-engineering","database_configured":true}"#.utf8)
        let health = try JSONDecoder().decode(FabrientAPI.Health.self, from: data)
        XCTAssertTrue(health.ok)
        XCTAssertEqual(health.service, "fabrient-engineering")
        XCTAssertEqual(health.databaseConfigured, true)
    }
}
