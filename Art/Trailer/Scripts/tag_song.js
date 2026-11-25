// Writes ID3v2.3 tags, lyrics and the cover into the song.
// Usage: node tag_song.js
// Reads Audio/song_a.mp3 and Out/kudakh_harder_cover.jpg, writes
// Out/kudakh_harder_song.mp3 and Out/kudakh_harder_song.lrc.
const fs = require("fs");
const path = require("path");

const trailer = path.join(__dirname, "..");
const lines = [
  [16.2, "Left the coop with the lights turned low,"],
  [20.1, "a borrowed car and a radio."],
  [24.0, "Every sign says eat in, take away,"],
  [27.9, "not this chick, not today."],
  [39.5, "Kudakh, kudakh, the road is long,"],
  [43.4, "the fryer's hot, but I am gone."],
  [47.3, "No bun, no pita, no lavash,"],
  [51.2, "to co-co-cosmos, I'll be kudakh!"],
  [55.1, "Kudakh, kudakh, the road is long,"],
  [59.0, "to co-co-cosmos, I'll be kudakh!"]];
const tags = {
  TIT2: "Kudakh Harder",
  TPE1: "The Ambitious Chicken",
  TPE2: "The Ambitious Chicken",
  TALB: "Ambitious Chicken 2: Kudakh Harder",
  TYER: "2026",
  TCON: "Road Rock",
  TRCK: "1/1",
  TLAN: "eng",
  TBPM: "123" };
const lyrics = lines.slice(0, 4).map((line) => line[1]).join("\n") +
  "\n\n" + lines.slice(4).map((line) => line[1]).join("\n");

function frame(id, data) {
  const head = Buffer.alloc(10);
  head.write(id, 0, "latin1");
  head.writeUInt32BE(data.length, 4);
  return Buffer.concat([head, data]);
}

function text(value) {
  return Buffer.concat([Buffer.from([0]), Buffer.from(value, "latin1")]);
}

const frames = Object.entries(tags).map(([id, value]) =>
  frame(id, text(value)));
frames.push(frame("USLT", Buffer.concat([
  Buffer.from([0]), Buffer.from("eng\0", "latin1"),
  Buffer.from(lyrics, "latin1")])));
frames.push(frame("COMM", Buffer.concat([
  Buffer.from([0]), Buffer.from("eng\0", "latin1"),
  Buffer.from("Song from the Ambitious Chicken 2 teaser trailer.",
    "latin1")])));
frames.push(frame("APIC", Buffer.concat([
  Buffer.from([0]), Buffer.from("image/jpeg\0", "latin1"),
  Buffer.from([3, 0]),
  fs.readFileSync(path.join(trailer, "Out", "kudakh_harder_cover.jpg"))])));
const body = Buffer.concat(frames);
const header = Buffer.from([0x49, 0x44, 0x33, 3, 0, 0,
  (body.length >> 21) & 127, (body.length >> 14) & 127,
  (body.length >> 7) & 127, body.length & 127]);

// Drop any tag the source already has.
let audio = fs.readFileSync(path.join(trailer, "Audio", "song_a.mp3"));
if (audio.slice(0, 3).toString("latin1") === "ID3") {
  const size = (audio[6] << 21) | (audio[7] << 14) | (audio[8] << 7) |
    audio[9];
  audio = audio.slice(10 + size);
}
fs.writeFileSync(path.join(trailer, "Out", "kudakh_harder_song.mp3"),
  Buffer.concat([header, body, audio]));

const stamp = (seconds) => {
  const minutes = Math.floor(seconds / 60);
  const rest = (seconds - minutes * 60).toFixed(2).padStart(5, "0");
  return "[" + String(minutes).padStart(2, "0") + ":" + rest + "]";
};
fs.writeFileSync(path.join(trailer, "Out", "kudakh_harder_song.lrc"),
  "[ti:" + tags.TIT2 + "]\n[ar:" + tags.TPE1 + "]\n[al:" + tags.TALB +
  "]\n" + lines.map((line) => stamp(line[0]) + line[1]).join("\n") + "\n");
console.log("tagged", body.length, "bytes of tags");
