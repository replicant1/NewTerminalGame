// Print, as JSON, every on-screen window the window server holds for one process.
// Test support for the shell's desktop tests: `swift tests/shell_windows.swift <pid>`.
// Reads the window list only; it cannot move, focus or close anything.
import CoreGraphics
import Foundation

let pid = Int32(CommandLine.arguments[1])!
let info = CGWindowListCopyWindowInfo([.optionOnScreenOnly], kCGNullWindowID) as? [[String: Any]] ?? []
var out: [[String: Any]] = []
for w in info {
    guard let owner = w[kCGWindowOwnerPID as String] as? Int32, owner == pid else { continue }
    let b = w[kCGWindowBounds as String] as? [String: Any] ?? [:]
    out.append([
        "id": w[kCGWindowNumber as String] as? Int ?? -1,
        "layer": w[kCGWindowLayer as String] as? Int ?? -1,
        "name": w[kCGWindowName as String] as? String ?? "",
        "x": b["X"] as? Double ?? 0, "y": b["Y"] as? Double ?? 0,
        "width": b["Width"] as? Double ?? 0, "height": b["Height"] as? Double ?? 0,
    ])
}
let data = try! JSONSerialization.data(withJSONObject: out, options: [.sortedKeys])
print(String(data: data, encoding: .utf8)!)
