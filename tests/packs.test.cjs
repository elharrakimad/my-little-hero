const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const catalogue=JSON.parse(fs.readFileSync('packs.json','utf8'));
const makeNode=()=>({value:'',textContent:'',innerHTML:'',hidden:false,disabled:false,files:[],dataset:{},style:{},classList:{toggle(){},remove(){}},events:{},addEventListener(e,f){this.events[e]=f},querySelector(){return null},setAttribute(){},scrollIntoView(){},focus(){},setCustomValidity(){},checkValidity(){return true}});
test('catalogue agrees with generated browser data and both public pack grids',()=>{
 const context={window:{}};vm.runInNewContext(fs.readFileSync('packs.js','utf8'),context);
 assert.deepEqual(JSON.parse(JSON.stringify(Object.values(context.window.MLH_PACKS))),catalogue);
 for(const file of ['index.html','web/index.html']){
  const html=fs.readFileSync(file,'utf8');
  for(const p of catalogue){
   assert.match(html,new RegExp(`data-wizard-pack="${p.id}"><b>${p.name}</b><span>${p.price} DH`));
   assert.match(html,new RegExp(`<h3>${p.name}</h3><div class="price">${p.price} `));
  }
  assert.match(html,/Livraison séparée/);
 }
});
for(const offer of catalogue)test(`${offer.name}: selection, preview payload, summary and WhatsApp`,async()=>{
 const ids=new Map();const get=id=>{if(!ids.has(id))ids.set(id,makeNode());return ids.get(id)};
 const packButtons=catalogue.map(p=>Object.assign(makeNode(),{dataset:{pack:p.id}}));
 const choices=catalogue.map(p=>Object.assign(makeNode(),{dataset:{wizardPack:p.id}}));
 const themes=['Science','Nature'].map(t=>Object.assign(makeNode(),{dataset:{theme:t}}));
 const next=[1,2,3].map(i=>Object.assign(makeNode(),{closest:()=>({dataset:{step:i}})}));
 let payload,url;
 const document={documentElement:{lang:'fr'},getElementById:get,querySelectorAll:s=>({'.wizard-card':[makeNode(),makeNode(),makeNode(),makeNode()],'.steps-labels span':[], '[data-pack]':packButtons,'[data-wizard-pack]':choices,'.choice':choices,'.next':next,'.back':[],'.theme-choice-grid button':themes}[s]||[]),addEventListener(e,fn){if(e==='DOMContentLoaded')fn()}};
 const window={MLH_PACKS:Object.fromEntries(catalogue.map(p=>[p.id,p])),matchMedia:()=>({matches:true}),generateStoryPreview:async p=>{payload=p;return true},open:u=>{url=u}};
 vm.runInNewContext(fs.readFileSync('script.js','utf8').split('\n')[0],{window,document,alert:m=>assert.fail(m)});
 packButtons[offer.id-1].events.click();
 assert.equal(get('summaryPack').textContent,offer.name);
 assert.equal(get('summaryPrice').textContent,`${offer.price} DH`);
 assert.equal(get('summaryContents').textContent,offer.contents);
 await next[0].events.click();
 for(const [id,value] of Object.entries({childName:'Adam',childAge:'7 ans',language:'Français',childGender:'boy',parentPhone:'0612345678'}))get(id).value=value;
 get('childPhoto').files=[{}];
 await next[1].events.click();
 for(let i=0;i<offer.styles.length;i++)themes[i].events.click();
 await next[2].events.click();
 assert.equal(payload.pack,offer.id);
 assert.equal(payload.themes.length,offer.styles.length);
 assert.equal(payload.bookStyle,offer.styles[0]);
 get('orderButton').events.click();
 const message=decodeURIComponent(url);
 assert.ok(message.includes(offer.contents));
 assert.ok(message.includes(`${offer.price} DH`));
 assert.match(message,/Livraison : séparée/);
});
