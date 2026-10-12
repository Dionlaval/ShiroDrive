// Usage: bundled-node raster_preview.cjs OUTPUT_DIRECTORY
const path = require('path');
const sharp = require('/Users/dionlava/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const dir = process.argv[2];
Promise.all(['front', 'back', 'overview'].map(n => sharp(path.join(dir,n+'.svg')).png().toFile(path.join(dir,n+'.png'))))
  .then(r=>console.log(JSON.stringify(r.map(x=>({width:x.width,height:x.height,size:x.size})))))
  .catch(e=>{console.error(e.message);process.exitCode=1});
