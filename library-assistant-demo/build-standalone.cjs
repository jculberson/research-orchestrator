// Inlines styles.css + app.js into a single shareable HTML file.
const fs = require('fs');
let html = fs.readFileSync('index.html','utf8');
const css = fs.readFileSync('styles.css','utf8');
const js  = fs.readFileSync('app.js','utf8');
html = html.replace('<link rel="stylesheet" href="styles.css" />', '<style>\n'+css+'\n</style>');
html = html.replace('<script src="app.js"></script>', '<script>\n'+js+'\n</script>');
html = html.replace('<title>Fort Smith Public Library — Concept Demo</title>',
  '<title>Fort Smith Public Library — Library Magic Assistant (Concept Demo)</title>');
fs.writeFileSync('library-magic-assistant-demo.html', html);
console.log('wrote library-magic-assistant-demo.html', html.length, 'bytes');
