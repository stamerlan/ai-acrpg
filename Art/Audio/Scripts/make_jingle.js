// Writes Art/Audio/SW_KebabJingle.wav: the All-Seeing Doner's kebab stand
// jingle, a short chiptune (square lead, triangle bass), 22.05 kHz mono.
// Run: node Art/Audio/Scripts/make_jingle.js
const fs = require("fs");
const path = require("path");

const RATE = 22050;
const BPM = 168;
const BEAT = 60 / BPM;
// [note, beats]; null is a rest. Bright "come and get it" motif.
const LEAD = [
  ["E5", 0.5], ["G5", 0.5], ["C6", 1], ["B5", 0.5], ["G5", 0.5],
  ["A5", 1], ["F5", 0.5], ["A5", 0.5], ["G5", 1], [null, 0.5],
  ["E5", 0.5], ["F5", 0.5], ["G5", 0.5], ["C6", 0.5], ["D6", 0.5],
  ["E6", 2],
];
const BASS = [
  ["C3", 1], ["G3", 1], ["F3", 1], ["C3", 1], ["F3", 1], ["G3", 1],
  ["C3", 1], ["G3", 0.5], ["C3", 1.5],
];
const SEMI = { C: -9, D: -7, E: -5, F: -4, G: -2, A: 0, B: 2 };

function freq(note) {
  const oct = Number(note.slice(-1));
  return 440 * Math.pow(2, (SEMI[note[0]] + (oct - 4) * 12) / 12);
}

function render(seq, wave, gain, out) {
  let t = 0;
  for (const [note, beats] of seq) {
    const len = beats * BEAT;
    const start = Math.round(t * RATE);
    const n = Math.round(len * RATE);
    if (note) {
      const f = freq(note);
      for (let i = 0; i < n && start + i < out.length; i++) {
        const ph = (i * f / RATE) % 1;
        const v = wave === "square" ? (ph < 0.5 ? 1 : -1)
          : 4 * Math.abs(ph - 0.5) - 1;
        const env = Math.min(1, i / 60) * Math.min(1, (n - i) / 400);
        out[start + i] += v * gain * env;
      }
    }
    t += len;
  }
}

const total = Math.ceil(LEAD.reduce((s, [, b]) => s + b, 0) * BEAT * RATE);
const mix = new Float32Array(total + RATE / 4);
render(LEAD, "square", 0.22, mix);
render(BASS, "triangle", 0.35, mix);
const data = Buffer.alloc(mix.length * 2);
for (let i = 0; i < mix.length; i++) {
  const s = Math.max(-1, Math.min(1, mix[i]));
  data.writeInt16LE(Math.round(s * 32767), i * 2);
}
const head = Buffer.alloc(44);
head.write("RIFF", 0);
head.writeUInt32LE(36 + data.length, 4);
head.write("WAVEfmt ", 8);
head.writeUInt32LE(16, 16);
head.writeUInt16LE(1, 20);
head.writeUInt16LE(1, 22);
head.writeUInt32LE(RATE, 24);
head.writeUInt32LE(RATE * 2, 28);
head.writeUInt16LE(2, 32);
head.writeUInt16LE(16, 34);
head.write("data", 36);
head.writeUInt32LE(data.length, 40);
const file = path.join(__dirname, "..", "SW_KebabJingle.wav");
fs.writeFileSync(file, Buffer.concat([head, data]));
console.log(file, (mix.length / RATE).toFixed(2) + " s");
