import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {Presentation,PresentationFile} from '@oai/artifact-tool';
import {slides} from './content.mjs';
import sharp from 'sharp';
import {createCanvas} from '@napi-rs/canvas';
import {resolvePresentationFont,finalizePresentation,applyPresentationChartFont} from '/Users/dionlava/.codex/plugins/cache/openai-primary-runtime/presentations/26.904.11930/skills/presentations/container_tools/artifact_tool_utils.mjs';
const dir=path.dirname(fileURLToPath(import.meta.url));
const skill='/Users/dionlava/.codex/plugins/cache/openai-primary-runtime/presentations/26.904.11930/skills/presentations';
const runtime='/Users/dionlava/.cache/codex-runtimes/codex-primary-runtime/dependencies';
const family=resolvePresentationFont();
const W=1600,H=900;
const C={bg:'#F8F7F3',ink:'#142F36',muted:'#49626B',teal:'#087F83',warm:'#926327'};
const pres=Presentation.create({slideSize:{width:W,height:H}});
const cropinfo=JSON.parse(await fs.readFile(path.join(dir,'crops.json'),'utf8'));
const tables=[];const charts=[];
const ctx=createCanvas(10,10).getContext('2d');
function lines(value,width,size,bold=false){ctx.font=`${bold?'bold ':''}${size}px "${family}"`;let count=0;for(const para of value.split('\n')){let line='';for(const word of para.split(' ')){const next=line?line+' '+word:word;if(ctx.measureText(next).width>width && line){count++;line=word;}else line=next;}count++;}return count;}
async function blocks(slide,data){
const items=[];const width=510;
for(const [head,body] of data){items.push([text(slide,head,1030,163,width,90,30,true,C.teal),text(slide,body,1030,265,width,180,28),head,body]);}
const layout=JSON.parse(await (await slide.export({format:'layout'})).text());
let y=163;
for(const [hs,bs,head,body] of items){
 const hn=layout.elements.find(e=>e.name===head.slice(0,60)).textLayout.lineCount;
 const bn=layout.elements.find(e=>e.name===body.slice(0,60)).textLayout.lineCount;
 const hh=hn*36,bh=bn*34;
 hs.position={left:1030,top:y,width,height:hh+5};bs.position={left:1030,top:y+hh+12,width,height:bh+5};
 y+=hh+12+bh+25;
}
if(y>778)console.log('CONTENT HEIGHT',y,data[0][0]);
}
function linechart(s,kind){
const temps=[20,30,40,50,60,70,80,90,100,110,120];
const values=temps.map(t=>{const r=10000*Math.exp(3380*(1/(t+273.15)-1/298.15));return Number((3.3*r/(4700+r)).toFixed(6));});
const c=s.charts.add('line',{position:{left:78,top:474,width:870,height:277},title:'Nominal NTC divider response',titleTextStyle:{typeface:family,fontSize:23,fill:C.ink},categories:temps.map(t=>String(t)),series:[{name:'ADC voltage',values,line:{fill:C.teal,width:3},marker:{symbol:'circle',size:4}}],hasLegend:false,xAxis:{title:{text:'Temperature (°C)',textStyle:{typeface:family,fontSize:20}},textStyle:{typeface:family,fontSize:18,fill:C.muted}},yAxis:{numberFormatCode:'0.0',min:0,max:3.3,title:{text:'V',textStyle:{typeface:family,fontSize:20}},textStyle:{typeface:family,fontSize:18,fill:C.muted},majorGridlines:{fill:'#CCD8D6',width:1}},chartFill:C.bg,plotAreaFill:C.bg});applyPresentationChartFont(c,{fontFamily:family});return c;}
function text(slide,value,x,y,w,h,size=30,bold=false,color=C.ink){
 const sh=slide.shapes.add({geometry:'textbox',name:value.slice(0,60),position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 sh.text=value;sh.text.style={typeface:family,fontSize:size,bold,color,autoFit:'none',verticalAlignment:'top',insets:{top:0,bottom:0,left:0,right:0}};return sh;
}
async function img(slide,key,x,y,w,h){
 const source=path.join(dir,'assets',key+'.png');
 const meta=await sharp(source).metadata();const r=Math.min(w/meta.width,h/meta.height);const dw=Math.round(meta.width*r),dh=Math.round(meta.height*r);
 const data=await sharp(source).resize(dw,dh,{kernel:'lanczos3'}).png().toBuffer();
 slide.images.add({blob:new Uint8Array(data),contentType:'image/png',alt:`KiCad source page ${cropinfo[key][0]}, ${key} circuit crop`,fit:'contain',position:{left:Math.round(x+(w-dw)/2),top:Math.round(y+(h-dh)/2),width:dw,height:dh}});
}
function table(slide,values,x,y,w,h,compact=false){
 const tab=slide.tables.add({rows:values.length,columns:values[0].length,left:x,top:y,width:w,height:h,values,columnTracks:values[0].map((_,i)=>({mode:'fr',value:i===values[0].length-1?1.55:1}))});
 tab.borders.assign({fill:'#D8DFDB',width:0.6});
 tab.cells.block({row:0,column:0,rowCount:values.length,columnCount:values[0].length}).assign({fill:C.bg,textStyle:{typeface:family,fontSize:compact?23:26,color:C.ink},margins:{left:13,right:13,top:10,bottom:9}});
 for(let i=0;i<values[0].length;i++){const c=tab.getCell(0,i);c.fill=C.ink;c.text.style={typeface:family,fontSize:compact?24:27,bold:true,color:'#FFFFFF'};}
 for(let r=1;r<values.length;r++){if(r%2===0)tab.cells.block({row:r,column:0,rowCount:1,columnCount:values[0].length}).fill='#EEF1ED';}
 return tab;
}
const sourceCommon='\n\nPRIMARY PROJECT SOURCES\nShiroFOC/ShiroFOC_KiCad/outputs/ShiroFOC_Rev_A_Schematic.pdf (A1-Drawing, 16 September 2026)\nShiroFOC/ShiroFOC_KiCad/outputs/ShiroFOC_Rev_A_BOM.csv\nShiroFOC/DESIGN_REVIEW_REV_A.md\nShiroFOC/FIRMWARE_BRINGUP_CONTRACT.md\nValues are released schematic/BOM values unless marked as examples. Engineering reasoning beyond recorded intent is interpretation. No hardware qualification is implied.';
await fs.mkdir(path.join(dir,'render'),{recursive:true});
for(let i=0;i<slides.length;i++){
 const d=slides[i],s=pres.slides.add(); s.background.fill=C.bg;
 const num=i<36?String(i+1).padStart(2,'0'):'A'+(i-35);
 text(s,d.title,58,42,1475,87,d.title.length>54?43:47,true);
 text(s,num,1490,833,60,31,21,false,C.muted);
 const caption=d.img?`KiCad schematic, page ${cropinfo[d.img][0]}${d.second?' + '+cropinfo[d.second][0]:''}`:'ShiroFOC engineering review';
 text(s,caption,60,837,1360,25,17,false,C.muted);
 if(d.cover){
   text(s,'Schematic topology and component decisions',60,132,1440,55,32,false,C.teal);
   await img(s,d.img,650,224,885,510);
   text(s,d.blocks[0][0],60,267,540,50,34,true);
   text(s,d.blocks[0][1],60,325,520,150,31);
   text(s,d.blocks[1][0],60,535,540,42,28,true,C.teal);
   text(s,d.blocks[1][1],60,587,520,100,26,false,C.muted);
   text(s,'Prototype targets. Hardware qualification remains open.',60,760,1420,55,27,false,C.warm);
 }else if(d.tableFull){
   table(s,d.table,60,151,1480,600,!!d.compact);tables.push(i+1);
   text(s,d.formula,60,778,1460,55,24,true,C.teal);
 }else if(d.table){
   table(s,d.table,60,163,925,348,true);tables.push(i+1);
   await img(s,d.img,60,542,925,203);
   await blocks(s,d.blocks);
   text(s,d.formula,60,777,1460,56,25,true,C.teal);
 }else if(!d.img){
   let y=167;for(const [head,body] of d.blocks){text(s,head,60,y,440,80,33,true,C.teal);text(s,body,525,y,1010,115,32);y+=188;}
   text(s,d.formula,60,778,1460,58,25,true,C.teal);
 }else{
   if(i===22){await img(s,d.img,90,156,855,300);linechart(s,'ntc');charts.push(i+1);}
   else if(d.second){await img(s,d.img,60,154,925,300);await img(s,d.second,60,478,925,272);}
   else await img(s,d.img,60,157,925,588);
   await blocks(s,d.blocks);
   text(s,d.formula,60,777,1460,57,25,true,C.teal);
 }
 const notes=d.notes+sourceCommon+(d.img?`\nIMAGE SOURCE: PDF page ${cropinfo[d.img][0]}, crop ${d.img}.`:'');
 s.speakerNotes.textFrame.setText(notes);
}
const candidate=path.join(dir,'candidate.pptx');
await (await PresentationFile.exportPptx(pres)).save(candidate);
console.log('Exported draft with',slides.length,'slides. Font:',family);
await fs.writeFile(path.join(dir,'deck.proto.json'),JSON.stringify(pres.toProto()));
for(let i=0;i<pres.slides.items.length;i++){
 const s=pres.slides.items[i];
 const b=await pres.export({slide:s,format:'png',scale:1});await fs.writeFile(path.join(dir,'render',`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await b.arrayBuffer()));
 const l=await s.export({format:'layout'});await fs.writeFile(path.join(dir,'render',`slide-${String(i+1).padStart(2,'0')}.json`),await l.text());
 console.log('Rendered',i+1);
}
await fs.writeFile(path.join(dir,'requirements.json'),JSON.stringify({font:family,tables,charts}));
console.log('Draft and previews ready.');
