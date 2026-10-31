const {test}=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');
const context={window:{},document:{addEventListener(){} }};
vm.createContext(context);
vm.runInContext(fs.readFileSync('theme-catalog.js','utf8'),context);
vm.runInContext(fs.readFileSync('themes.js','utf8'),context);
const {MLH_THEME_CATALOG:catalog,MLH_THEME_CATEGORIES:categories,MLHThemeSearch:search}=context.window;

test('239 distinct themes in 18 bilingual categories, with stable legacy values',()=>{
  assert.equal(catalog.length,239);assert.equal(categories.length,18);
  assert.equal(new Set(catalog.map(t=>t.label)).size,239);
  assert.equal(new Set(catalog.map(t=>t.theme)).size,239);
  for(const c of categories){assert.ok(c.ar);assert.ok(catalog.filter(t=>t.category===c.id).length>=12);}
  assert.ok(catalog.every(t=>t.ar&&t.icon&&categories.some(c=>c.id===t.category)));
  assert.equal(catalog.find(t=>t.label==='Espace').theme,"🚀 Voyage dans l'espace");
  assert.equal(catalog.find(t=>t.label==='Pâtisserie').theme,'🍰 Aventure de pâtisserie');
});

test('profile suggestions never prevent access to any category or theme',()=>{
  const girl=search.filter(catalog,{gender:'girl'});
  assert.ok(girl.some(t=>t.label==='Fées'));assert.ok(!girl.some(t=>t.label==='Robots'));
  const boy=search.filter(catalog,{gender:'boy'});
  assert.ok(boy.some(t=>t.label==='Robots'));assert.ok(!boy.some(t=>t.label==='Fées'));
  assert.equal(search.filter(catalog,{gender:'girl',showAll:true}).length,239);
  assert.equal(search.filter(catalog,{gender:'boy',showAll:true}).length,239);
});

test('search ignores French accents, works in Arabic, and combines category filters',()=>{
  assert.ok(search.filter(catalog,{query:'veterinaire',showAll:true}).some(t=>t.label.includes('vétérinaire')));
  assert.ok(search.filter(catalog,{query:'بيطري',showAll:true}).some(t=>t.label.includes('vétérinaire')));
  const matches=search.filter(catalog,{category:'space',showAll:true});
  assert.equal(matches.length,13);assert.ok(matches.every(t=>t.category==='space'));
  assert.ok(search.filter(catalog,{query:'pays emotions',showAll:true}).some(t=>t.label==='Le pays des émotions'));
  assert.equal(search.filter(catalog,{query:'zzzznoresult',showAll:true}).length,0);
});


test('distinct superpowers and a dedicated girls category remain accessible to everyone',()=>{
  const powers=search.filter(catalog,{category:'superpowers',showAll:true});
  const heroines=search.filter(catalog,{category:'heroines',showAll:true});
  assert.equal(powers.length,20);assert.equal(heroines.length,20);
  assert.ok(powers.some(t=>t.label.includes('invisibilité')));
  assert.ok(powers.some(t=>t.label.includes('téléportation')));
  assert.ok(search.filter(catalog,{gender:'girl'}).some(t=>t.category==='heroines'));
  assert.ok(!search.filter(catalog,{gender:'boy'}).some(t=>t.category==='heroines'));
  assert.equal(search.filter(catalog,{gender:'boy',category:'heroines',showAll:true}).length,20);
});
