import Foundation
import Vision

guard CommandLine.arguments.count == 2 else {
    FileHandle.standardError.write(Data("Usage: swift recognize_text.swift IMAGE\n".utf8))
    exit(2)
}

let imageURL = URL(fileURLWithPath: CommandLine.arguments[1])
let request = VNRecognizeTextRequest()
request.recognitionLevel = .accurate
request.recognitionLanguages = ["zh-Hans", "en-US"]
try VNImageRequestHandler(url: imageURL).perform([request])
for observation in request.results ?? [] {
    if let line = observation.topCandidates(1).first {
        print(line.string)
    }
}
