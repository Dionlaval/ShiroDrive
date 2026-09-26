import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {finalizePresentation} from '/Users/dionlava/.codex/plugins/cache/openai-primary-runtime/presentations/26.904.11930/skills/presentations/container_tools/artifact_tool_utils.mjs';
const dir=path.dirname(fileURLToPath(import.meta.url));
const skill='/Users/dionlava/.codex/plugins/cache/openai-primary-runtime/presentations/26.904.11930/skills/presentations';
const {font,tables,charts}=JSON.parse(await fs.readFile(path.join(dir,'requirements.json')));
console.log(await finalizePresentation({workspaceDir:path.dirname(dir),candidatePath:path.join(dir,'candidate.pptx'),finalPath:path.join(dir,'../output/ShiroFOC_Design_Review.pptx'),pythonExecutable:'/Users/dionlava/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3',integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','15240000,8572500','--validate-bullet-geometry','--validate-heading-fit',...tables.flatMap(n=>['--require-native-table-slide',String(n)])],explicitTotalSlideCount:41,requiredNativeTableOwnerSlides:tables,requiredNativeChartOwnerSlides:charts,fontPolicy:{basis:'design',families:[font]},materializeLiteralChartWorkbooks:true,verifyArtifactToolImport:true,receiptPath:path.join(dir,'validation.json')}));
