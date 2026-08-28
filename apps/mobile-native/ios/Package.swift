// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "FabrientMobile",
    platforms: [.iOS(.v17)],
    products: [.library(name: "FabrientMobile", targets: ["FabrientMobile"])],
    targets: [
        .target(name: "FabrientMobile"),
        .testTarget(name: "FabrientMobileTests", dependencies: ["FabrientMobile"]),
    ]
)
