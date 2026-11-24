// Writes the backpack item icons as SVG to ../Source and renders them to
// ../T_Item_<Name>.png (256 px) with headless Edge.
// Run: node make_icons.js
const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");

const EDGE = "C:\\Program Files (x86)\\Microsoft\\Edge\\" +
  "Application\\msedge.exe";
const SRC = path.join(__dirname, "..", "Source");
const OUT = path.join(__dirname, "..");
const BG = '<rect x="8" y="8" width="240" height="240" rx="28" ' +
  'fill="#3b2f24"/><rect x="8" y="8" width="240" height="240" rx="28" ' +
  'fill="none" ' +
  'stroke="#6b5640" stroke-width="6"/>';
const O = 'stroke="#1e1610" stroke-width="6" stroke-linejoin="round" ' +
  'stroke-linecap="round"';
const F = 'font-family="Arial Black, Arial" font-weight="900" ' +
  'text-anchor="middle"';

const kernels = [];
for (const [y, xs] of [[70, [112, 128, 144]], [93, [106, 122, 138, 152]],
  [119, [104, 120, 136, 152]], [145, [106, 122, 138, 152]],
  [171, [112, 128, 144]]]) {
  for (const x of xs) kernels.push(`<circle cx="${x}" cy="${y}" r="7"/>`);
}

const ICONS = {
  CornCob: `<g transform="rotate(-35 128 128)">
<path d="M128 40 C160 40 168 90 166 130 C164 180 150 214 128 214 C106 214
92 180 90 130 C88 90 96 40 128 40 Z" fill="#f4c430" ${O}/>
<g fill="#d99a1c">${kernels.join("")}</g>
<g fill="#5e3a1a" opacity="0.55"><circle cx="128" cy="92" r="9"/>
<circle cx="114" cy="146" r="8"/><circle cx="146" cy="160" r="8"/></g>
<path d="M128 214 C96 210 70 186 66 150 C84 170 104 186 128 192 Z"
fill="#7fb04a" ${O}/>
<path d="M128 214 C160 210 186 186 190 150 C172 170 152 186 128 192 Z"
fill="#6a9a3a" ${O}/>
<path d="M120 214 L118 236 L138 236 L136 214 Z" fill="#c9a26a" ${O}/></g>`,

  Checklist: `<g transform="rotate(-6 128 128)">
<rect x="58" y="34" width="140" height="188" rx="6" fill="#f3ead2" ${O}/>
<rect x="96" y="24" width="64" height="22" rx="6" fill="#9a7b55" ${O}/>
<g stroke="#8b7d63" stroke-width="5" stroke-linecap="round">
<line x1="78" y1="72" x2="178" y2="72"/><line x1="78" y1="168" x2="150"
y2="168"/>
<line x1="78" y1="186" x2="164" y2="186"/><line x1="78" y1="204" x2="130"
y2="204"/></g>
<g fill="none" stroke="#7a6a50" stroke-width="4">
<rect x="74" y="88" width="24" height="24"/><rect x="104" y="88" width="24"
height="24"/>
<rect x="134" y="88" width="24" height="24"/><rect x="164" y="88" width="24"
height="24"/></g>
<g transform="rotate(-14 120 132)">
<rect x="66" y="112" width="112" height="40" rx="5" fill="none"
stroke="#c0392b"
stroke-width="6"/>
<text x="122" y="131" ${F} font-size="15" fill="#c0392b">CARGO:</text>
<text x="122" y="147" ${F} font-size="15"
fill="#c0392b">POULTRY</text></g></g>`,

  TransitCard: `<g transform="rotate(-8 128 128)">
<rect x="34" y="66" width="188" height="124" rx="14" fill="#e8e3d6"/>
<path d="M48 66 L208 66 A14 14 0 0 1 222 80 L222 96 L34 96 L34 80 A14 14 0 0 1
48 66 Z" fill="#dc143c"/>
<rect x="34" y="66" width="188" height="124" rx="14" fill="none" ${O}/>
<text x="128" y="88" ${F} font-size="16" fill="#fff">TRANSIT - CARGO</text>
<rect x="50" y="106" width="56" height="66" rx="5" fill="#cfc6b0"
stroke="#7a6a50"
stroke-width="4"/>
<ellipse cx="78" cy="152" rx="18" ry="15" fill="#fbf8f0" stroke="#1e1610"
stroke-width="3"/>
<circle cx="82" cy="130" r="10" fill="#fbf8f0" stroke="#1e1610"
stroke-width="3"/>
<path d="M74 122 l4 -8 l4 7 l4 -7 l2 9 Z" fill="#d9302c"/>
<path d="M91 130 l9 3 l-9 3 Z" fill="#f2a020"/>
<rect x="76" y="126" width="13" height="4" fill="#111"/>
<g stroke="#8b7d63" stroke-width="5" stroke-linecap="round">
<line x1="120" y1="116" x2="204" y2="116"/><line x1="120" y1="132" x2="190"
y2="132"/></g>
<text x="162" y="170" ${F} font-size="16" fill="#1e1610">PL ONLY</text></g>`,

  CarKeys: `<circle cx="88" cy="84" r="26" fill="none" stroke="#1e1610"
stroke-width="16"/>
<circle cx="88" cy="84" r="26" fill="none" stroke="#c9ccd1" stroke-width="9"/>
<g transform="rotate(35 108 126)">
<rect x="86" y="96" width="44" height="60" rx="10" fill="#222" ${O}/>
<path d="M100 156 L100 220 L110 220 L110 210 L120 210 L120 200 L112 200 L112
190
L118 190 L118 180 L112 180 L112 156 Z" fill="#c9ccd1" ${O}/>
<circle cx="108" cy="118" r="6" fill="#c9ccd1"/></g>
<line x1="104" y1="96" x2="150" y2="128" stroke="#9a8a70" stroke-width="4"/>
<g transform="rotate(-18 176 150)">
<path d="M136 120 L204 120 L216 150 L204 180 L136 180 Z" fill="#f3e1a0" ${O}/>
<circle cx="202" cy="150" r="5" fill="#3b2f24"/>
<text x="168" y="147" ${F} font-size="14" fill="#1e1610">CIVIC</text>
<text x="168" y="166" ${F} font-size="12" fill="#c0392b">+1 HEN</text></g>`,

  ZbyszekBox: `<path d="M44 96 L128 66 L212 96 L212 194 L128 224 L44 194 Z"
fill="#c8955a" ${O}/>
<path d="M44 96 L128 126 L212 96 L128 66 Z" fill="#dcaa6e" ${O}/>
<path d="M128 126 L128 224" fill="none" ${O}/>
<g transform="rotate(18 86 162)">
<rect x="38" y="148" width="98" height="26" fill="#f2d21b" stroke="#1e1610"
stroke-width="4"/>
<text x="87" y="167" ${F} font-size="14" fill="#1e1610">EVIDENCE</text></g>
<text x="170" y="182" ${F} font-size="44" fill="#7a4a22"
transform="rotate(-18 170 166)">?</text>`,

  ForgedStamp: `<g transform="rotate(-12 128 196)">
<rect x="40" y="168" width="176" height="56" rx="6" fill="none"
stroke="#2a5db0"
stroke-width="7"/>
<text x="128" y="210" ${F} font-size="38" fill="#2a5db0">PERSON</text></g>
<ellipse cx="128" cy="50" rx="34" ry="22" fill="#8b3a1a" ${O}/>
<rect x="114" y="58" width="28" height="52" fill="#a0522d" ${O}/>
<rect x="74" y="108" width="108" height="26" rx="4" fill="#5b3a22" ${O}/>
<rect x="80" y="134" width="96" height="14" fill="#333" ${O}/>`,

  Gnomonaut: `<path d="M80 228 C78 172 92 142 128 142 C164 142 178 172 176 228
Z"
fill="#2f5fb3" ${O}/>
<rect x="84" y="184" width="88" height="12" fill="#5b3a22"/>
<circle cx="128" cy="116" r="36" fill="#f0c8a0" ${O}/>
<circle cx="128" cy="126" r="9" fill="#e59a86"/>
<circle cx="114" cy="108" r="5" fill="#1e1610"/>
<circle cx="142" cy="108" r="5" fill="#1e1610"/>
<path d="M98 126 C102 166 154 166 158 126 C146 142 110 142 98 126 Z"
fill="#f4f1ea" ${O}/>
<path d="M104 52 L128 4 L152 52 Z" fill="#d9302c" ${O}/>
<circle cx="128" cy="112" r="62" fill="#bfe4ff" fill-opacity="0.3"
stroke="#e6edf3" stroke-width="8"/>
<circle cx="128" cy="112" r="66" fill="none" stroke="#1e1610"
stroke-width="3"/>
<path d="M90 74 A46 46 0 0 1 140 58" fill="none" stroke="#ffffff"
stroke-width="7" stroke-linecap="round" opacity="0.8"/>`,
};

fs.mkdirSync(SRC, { recursive: true });
for (const [name, body] of Object.entries(ICONS)) {
  const svg = '<svg xmlns="http://www.w3.org/2000/svg" width="256" ' +
    `height="256" viewBox="0 0 256 256">${BG}${body}</svg>\n`;
  const file = path.join(SRC, name + ".svg");
  fs.writeFileSync(file, svg);
  const html = path.join(SRC, "_render.html");
  fs.writeFileSync(html, "<html><body " +
    'style="margin:0;background:transparent">' + svg + "</body></html>");
  execFileSync(EDGE, ["--headless", "--disable-gpu", "--hide-scrollbars",
    "--default-background-color=00000000", "--window-size=256,256",
    "--screenshot=" + path.join(OUT, "T_Item_" + name + ".png"),
    "file:///" + html.replace(/\\/g, "/")]);
  fs.unlinkSync(html);
  console.log(name);
}
