import AppKit
import Foundation
import PDFKit

guard CommandLine.arguments.count == 3 else {
    fputs("usage: render_pdf.swift INPUT.pdf OUTPUT_DIR\n", stderr)
    exit(2)
}

let inputURL = URL(fileURLWithPath: CommandLine.arguments[1])
let outputURL = URL(fileURLWithPath: CommandLine.arguments[2], isDirectory: true)

guard let document = PDFDocument(url: inputURL) else {
    fputs("could not open PDF: \(inputURL.path)\n", stderr)
    exit(1)
}

try FileManager.default.createDirectory(
    at: outputURL,
    withIntermediateDirectories: true
)

for pageIndex in 0..<document.pageCount {
    guard let page = document.page(at: pageIndex) else {
        fputs("could not read page \(pageIndex + 1)\n", stderr)
        exit(1)
    }

    let box = page.bounds(for: .mediaBox)
    let targetSize = NSSize(width: box.width * 2, height: box.height * 2)
    let image = page.thumbnail(of: targetSize, for: .mediaBox)
    guard
        let tiff = image.tiffRepresentation,
        let bitmap = NSBitmapImageRep(data: tiff),
        let png = bitmap.representation(using: .png, properties: [:])
    else {
        fputs("could not rasterize page \(pageIndex + 1)\n", stderr)
        exit(1)
    }

    let name = String(format: "page-%02d.png", pageIndex + 1)
    try png.write(to: outputURL.appendingPathComponent(name))
}

print("rendered \(document.pageCount) pages")
