import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {FileBlob,PresentationFile} from '@oai/artifact-tool';
import '/Users/dionlava/.codex/plugins/cache/openai-primary-runtime/presentations/26.904.11930/skills/presentations/container_tools/artifact_tool_utils.mjs';
const dir=path.dirname(fileURLToPath(import.meta.url));
const p=await PresentationFile.importPptx(await FileBlob.load(path.join(dir,'../output/ShiroFOC_Design_Review.pptx')));
await fs.mkdir(path.join(dir,'render-final'),{recursive:true});
for(let i=0;i<p.slides.items.length;i++){
 const s=p.slides.items[i];
 const b=await p.export({slide:s,format:'png',scale:1});
 await fs.writeFile(path.join(dir,'render-final',`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await b.arrayBuffer()));
 console.log('Rendered',i+1);
}
