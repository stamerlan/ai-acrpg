// Calls a Google generative model and saves the media it returns.
// Usage: GKEY=<key> node gen.js <model> <request.json> <out-base>
// request.json: { "prompt": "...", "images": ["path", ...],
//                 "config": { generationConfig fields } }
// Writes <out-base>.<ext> per returned media part and prints any text.
const fs = require("fs");
const path = require("path");

const [model, requestPath, outBase] = process.argv.slice(2);
const request = JSON.parse(fs.readFileSync(requestPath, "utf8"));
const mimeOf = { ".png": "image/png", ".jpg": "image/jpeg",
  ".wav": "audio/wav", ".mp3": "audio/mpeg", ".mp4": "video/mp4" };
const extOf = { "image/png": "png", "image/jpeg": "jpg",
  "audio/wav": "wav", "audio/mpeg": "mp3", "audio/mp3": "mp3",
  "video/mp4": "mp4" };

const parts = [{ text: request.prompt }];
for (const file of request.images || request.files || []) {
  parts.push({ inlineData: {
    mimeType: mimeOf[path.extname(file).toLowerCase()],
    data: fs.readFileSync(file).toString("base64") } });
}
const body = { contents: [{ role: "user", parts }] };
if (request.config) body.generationConfig = request.config;

const url = "https://generativelanguage.googleapis.com/v1beta/models/" +
  model + ":generateContent";
fetch(url, {
  method: "POST",
  headers: { "x-goog-api-key": process.env.GKEY,
    "Content-Type": "application/json" },
  body: JSON.stringify(body),
}).then(async (response) => {
  const reply = await response.json();
  if (!response.ok) {
    console.error(JSON.stringify(reply, null, 1).slice(0, 2000));
    process.exit(1);
  }
  let count = 0;
  for (const candidate of reply.candidates || []) {
    for (const part of (candidate.content || {}).parts || []) {
      if (part.text) console.log(part.text);
      if (!part.inlineData) continue;
      const mime = part.inlineData.mimeType.split(";")[0];
      const data = Buffer.from(part.inlineData.data, "base64");
      let ext = extOf[mime];
      let bytes = data;
      if (!ext && mime.startsWith("audio/")) {
        // Raw 16-bit PCM (audio/L16): wrap it in a WAV header.
        const rate = Number(
          (/rate=(\d+)/.exec(part.inlineData.mimeType) || [0, 24000])[1]);
        const header = Buffer.alloc(44);
        header.write("RIFF", 0);
        header.writeUInt32LE(36 + data.length, 4);
        header.write("WAVEfmt ", 8);
        header.writeUInt32LE(16, 16);
        header.writeUInt16LE(1, 20);
        header.writeUInt16LE(1, 22);
        header.writeUInt32LE(rate, 24);
        header.writeUInt32LE(rate * 2, 28);
        header.writeUInt16LE(2, 32);
        header.writeUInt16LE(16, 34);
        header.write("data", 36);
        header.writeUInt32LE(data.length, 40);
        bytes = Buffer.concat([header, data]);
        ext = "wav";
      }
      const suffix = count ? "_" + count : "";
      const file = outBase + suffix + "." + (ext || "bin");
      fs.writeFileSync(file, bytes);
      console.log("saved " + file + " (" + part.inlineData.mimeType + ")");
      count += 1;
    }
  }
  if (!count) console.log(JSON.stringify(reply).slice(0, 1500));
});
