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
