const {test}=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');

test('local file preview gives a useful message without a billable API request', async()=>{
  const node={setAttribute(){}};
  const alerts=[];
  const window={location:{protocol:'file:'}};
  const document={
    addEventListener:(_,handler)=>handler(),
    getElementById:()=>node,
    documentElement:{lang:'fr'},
  };
  vm.runInNewContext(fs.readFileSync('preview.js','utf8'),{
    window,document,alert:message=>alerts.push(message),
    fetch:()=>assert.fail('file previews must not call the API'),
    FormData:class {constructor(){assert.fail('must stop before constructing a request');}},
  });
  const result=await window.generateStoryPreview({name:'Test',age:7,gender:'girl',themes:['Science'],photoFile:{}});
  assert.equal(result,false);
  assert.match(alerts[0],/https:\/\/my-little-hero.online/);
  document.documentElement.lang='ar';
  await window.generateStoryPreview({});
  assert.match(alerts[1],/افتح الموقع/);
});

test('preview request includes parent contact and the custom description', async()=>{
  const node={setAttribute(){},removeAttribute(){}};
  const fields=new Map();
  const window={location:{protocol:'https:'}};
  const document={addEventListener:(_,fn)=>fn(),getElementById:()=>node,
    querySelector:()=>null,documentElement:{lang:'fr'}};
  let requested=false;
  vm.runInNewContext(fs.readFileSync('preview.js','utf8'),{
    window,document,alert(){},console:{error(){}},
    FormData:class {append(k,v){fields.set(k,v);}},
    fetch:async()=>{requested=true;return {ok:false,json:async()=>({detail:'Test: no generation'})};},
  });
  await window.generateStoryPreview({name:'Test',age:7,gender:'girl',themes:['✨ Mon propre thème'],
    photoFile:{},parentPhone:'+212612345678',parentEmail:'',customTheme:'Un jardin magique'});
  assert.equal(requested,true);
  assert.equal(fields.get('parent_phone'),'+212612345678');
  assert.equal(fields.get('parent_email'),'');
  assert.equal(fields.get('custom_theme'),'Un jardin magique');
  requested=false;
  await window.generateStoryPreview({name:'Test',age:7,gender:'girl',themes:['Science'],photoFile:{},parentPhone:''});
  assert.equal(requested,false);
});
