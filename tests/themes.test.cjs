const {test}=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');
const context={window:{},document:{addEventListener(){} }};
vm.createContext(context);
vm.runInContext(fs.readFileSync('theme-catalog.js','utf8'),context);
vm.runInContext(fs.readFileSync('themes.js','utf8'),context);
const {MLH_THEME_CATALOG:catalog,MLH_THEME_CATEGORIES:categories,MLHThemeSearch:search}=context.window;

test('279 distinct themes in 20 bilingual categories, with stable legacy values',()=>{
  assert.equal(catalog.length,279);assert.equal(categories.length,20);
  assert.equal(new Set(catalog.map(t=>t.label)).size,279);
  assert.equal(new Set(catalog.map(t=>t.theme)).size,279);
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
  assert.equal(search.filter(catalog,{gender:'girl',showAll:true}).length,279);
  assert.equal(search.filter(catalog,{gender:'boy',showAll:true}).length,279);
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


test('comic and anime inspirations are searchable and keep the personalized child as the hero',()=>{
  for(const category of ['comics','anime']){
    const rows=search.filter(catalog,{category,showAll:true});
    assert.equal(rows.length,20);
    assert.ok(rows.every(t=>t.theme.includes('Héros personnalisé')));
  }
  assert.ok(search.filter(catalog,{query:'Spider-Man',showAll:true}).some(t=>t.category==='comics'));
  assert.ok(search.filter(catalog,{query:'Naruto',showAll:true}).some(t=>t.category==='anime'));
  assert.ok(search.filter(catalog,{query:'ناروتو',showAll:true}).some(t=>t.category==='anime'));
});


test('displayed inspirations are separate from powers and visual descriptions sent to generation',()=>{
  const names=['Spider-Man','Iron Man','Thor','Hulk','Captain America','Doctor Strange','Black Panther','Ant-Man','Scarlet Witch','Superman','Batman','Wonder Woman','Flash','Aquaman','Green Lantern','Cyborg','Shazam','Supergirl','Zatanna','Goku','Naruto','Luffy','Tanjiro','Deku','Sailor Moon','Sacha','Pikachu','Sakura','Natsu','Edward Elric','Gon','Killua','Saitama','Ichigo','Yugi','Hinata','Tsubasa','Seiya','Astro Boy','Totoro'];
  const profiles=catalog.filter(t=>['comics','anime'].includes(t.category));
  assert.equal(profiles.length,40);
  assert.equal(new Set(profiles.map(t=>t.theme)).size,40);
  for(const profile of profiles){
    assert.ok(profile.theme.includes('Tenue et apparence :'));
    for(const name of names)assert.ok(!new RegExp('\\b'+name+'\\b','iu').test(profile.theme),profile.label+' leaked '+name);
  }
  assert.ok(profiles.some(t=>t.label.startsWith('Spider-Man')));
});


test('every inspiration includes a distinct world used by cover and story generation',()=>{
  const profiles=catalog.filter(t=>['comics','anime'].includes(t.category));
  assert.equal(profiles.length,40);
  assert.equal(new Set(profiles.map(t=>t.world.setting)).size,40);
  for(const profile of profiles){
    for(const key of ['setting','places','objects','mission']){
      assert.ok(profile.world[key].length>20);
      assert.ok(profile.theme.includes(profile.world[key]));
    }
    assert.ok(profile.theme.includes('dès la couverture'));
    assert.ok(profile.theme.includes('toute l’histoire'));
  }
  const city=profiles.find(t=>t.label.startsWith('Spider-Man'));
  assert.ok(city.world.setting.includes('métropole verticale'));
  const village=profiles.find(t=>t.label.startsWith('Naruto'));
  assert.ok(village.world.places.includes('académie'));
});


test('the forty written references include clothing, equipment and opponents or appropriate obstacles',()=>{
  const profiles=catalog.filter(t=>['comics','anime'].includes(t.category));
  for(const p of profiles){
    for(const key of ['costume','equipment','adversaries']){
      assert.ok(p.reference[key].length>40);
      assert.ok(p.theme.includes(p.reference[key]));
    }
    assert.ok(p.theme.includes('visage de l’enfant'));
    assert.ok(p.theme.includes('sans blessure ni scène sanglante'));
  }
  assert.ok(profiles.find(t=>t.label.startsWith('Spider-Man')).reference.costume.includes('rouge et bleue'));
  assert.ok(profiles.find(t=>t.label.startsWith('Batman')).reference.equipment.includes('grappin'));
  assert.ok(profiles.find(t=>t.label.startsWith('Totoro')).reference.adversaries.includes('aucun méchant'));
});
