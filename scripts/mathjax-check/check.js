const base = process.argv[2];
const {mathjax} = require(base + '/mathjax-full/js/mathjax.js');
const {TeX} = require(base + '/mathjax-full/js/input/tex.js');
const {SVG} = require(base + '/mathjax-full/js/output/svg.js');
const {liteAdaptor} = require(base + '/mathjax-full/js/adaptors/liteAdaptor.js');
const {RegisterHTMLHandler} = require(base + '/mathjax-full/js/handlers/html.js');
const {AllPackages} = require(base + '/mathjax-full/js/input/tex/AllPackages.js');
const fs = require('fs');
const adaptor = liteAdaptor(); RegisterHTMLHandler(adaptor);
const errors = [];
const tex = new TeX({packages: AllPackages.filter(p => p !== 'noundefined'),
  macros: {ring: ['\\mathring{#1}', 1]}, environments: {equationsbase: ['\\begin{aligned}', '\\end{aligned}']},
  formatError: (jax, err) => { errors.push(err.message); return jax.formatError(err); }});
const doc = mathjax.document('', {InputJax: tex, OutputJax: new SVG({fontCache: 'none'})});
const items = JSON.parse(fs.readFileSync(process.argv[3]));
const res = {};
for (const it of items) {
  errors.length = 0;
  try { doc.convert(it.tex, {display: it.display}); } catch (e) { errors.push('THROW ' + e.message); }
  for (const m of errors) { const k = m; (res[k] = res[k] || []).push(it.file + ': ' + it.tex.replace(/\s+/g,' ').slice(0, 160)); }
}
for (const [k, v] of Object.entries(res)) { console.log('### ' + k + '  (' + v.length + ')'); for (const x of v.slice(0, 6)) console.log('   ' + x); }
