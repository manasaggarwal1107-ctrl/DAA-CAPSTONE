// Production build: esbuild bundles the TypeScript/React app, Tailwind v4's compiler
// generates the stylesheet from the class names found in the source files.
//   node scripts/build.mjs            one-off build into ./dist
//   node scripts/build.mjs --watch    rebuild whenever a source file changes
import { build } from 'esbuild';
import { compile } from 'tailwindcss';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const src = path.join(root, 'src');
const dist = path.join(root, 'dist');
const watch = process.argv.includes('--watch');
const twRoot = path.join(root, 'node_modules', 'tailwindcss');

function walk(dir) {
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((e) =>
    e.isDirectory() ? walk(path.join(dir, e.name)) : [path.join(dir, e.name)]);
}

async function buildCss() {
  const input = fs.readFileSync(path.join(src, 'index.css'), 'utf8');
  const compiler = await compile(input, {
    base: src,
    loadStylesheet: async (id, base) => {
      const file = id === 'tailwindcss' ? path.join(twRoot, 'index.css')
        : id.startsWith('tailwindcss/') ? path.join(twRoot, id.slice('tailwindcss/'.length))
        : path.resolve(base, id);
      return { path: file, base: path.dirname(file), content: fs.readFileSync(file, 'utf8') };
    },
  });
  // Collect every token that could be a class name; unknown tokens are ignored by Tailwind.
  const files = [...walk(src).filter((f) => /\.(tsx?|css)$/.test(f)), path.join(root, 'index.html')];
  const candidates = new Set();
  for (const file of files) {
    for (const token of fs.readFileSync(file, 'utf8').match(/[^\s"'`<>{}(),;|\\]+/g) ?? []) candidates.add(token);
  }
  return compiler.build([...candidates]);
}

async function buildAll() {
  const started = Date.now();
  fs.rmSync(dist, { recursive: true, force: true });
  fs.mkdirSync(path.join(dist, 'assets'), { recursive: true });
  await build({
    entryPoints: [path.join(src, 'main.tsx')],
    bundle: true, minify: !watch, sourcemap: watch, target: 'es2020', format: 'iife',
    jsx: 'automatic', outfile: path.join(dist, 'assets', 'app.js'), logLevel: 'warning',
    define: { 'process.env.NODE_ENV': JSON.stringify(watch ? 'development' : 'production') },
  });
  fs.writeFileSync(path.join(dist, 'assets', 'app.css'), await buildCss());
  const stamp = Date.now();
  fs.writeFileSync(path.join(dist, 'index.html'),
    fs.readFileSync(path.join(root, 'index.html'), 'utf8').replaceAll('__BUILD__', String(stamp)));
  fs.copyFileSync(path.join(root, 'public', 'favicon.svg'), path.join(dist, 'favicon.svg'));
  const kb = (f) => (fs.statSync(path.join(dist, 'assets', f)).size / 1024).toFixed(0);
  console.log(`Built in ${Date.now() - started} ms  (app.js ${kb('app.js')} KB, app.css ${kb('app.css')} KB)`);
}

await buildAll();
if (watch) {
  let timer;
  const rebuild = () => { clearTimeout(timer); timer = setTimeout(() => buildAll().catch((e) => console.error(e.message)), 150); };
  fs.watch(src, { recursive: true }, rebuild);
  console.log('Watching src/ for changes - reload the browser after each rebuild.');
}
