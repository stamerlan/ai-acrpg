// Writes Art/Audio/SW_CarAlarm.wav: a two-tone car alarm (wee-oo) for
// Mr. Kebabski's charge into a car, 2.5 s, 22.05 kHz mono.
// Run: node Art/Audio/Scripts/make_car_alarm.js
const fs = require("fs");
const path = require("path");

const RATE = 22050;
const SECONDS = 2.5;
const n = Math.round(RATE * SECONDS);
const data = Buffer.alloc(n * 2);
let phase = 0;
for (let i = 0; i < n; i++) {
  const t = i / RATE;
  // Sweep up and down twice a second between 700 and 1300 Hz.
  const f = 1000 + 300 * Math.sin(2 * Math.PI * 2 * t);
  phase = (phase + f / RATE) % 1;
  const square = phase < 0.5 ? 1 : -1;
  const env = Math.min(1, t / 0.02) * Math.min(1, (SECONDS - t) / 0.1);
  data.writeInt16LE(Math.round(square * 0.25 * env * 32767), i * 2);
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
const file = path.join(__dirname, "..", "SW_CarAlarm.wav");
fs.writeFileSync(file, Buffer.concat([head, data]));
console.log(file, SECONDS + " s");
