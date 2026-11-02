const {test}=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');
const context={window:{},document:{addEventListener(){} }};
vm.createContext(context);
vm.runInContext(fs.readFileSync('theme-catalog.js','utf8'),context);
vm.runInContext(fs.readFileSync('themes.js','utf8'),context);
const {MLH_THEME_CATALOG:catalog,MLH_THEME_CATEGORIES:categories,MLHThemeSearch:search}=context.window;

test('315 distinct themes in 20 bilingual categories, with stable legacy values',()=>{
  assert.equal(catalog.length,315);assert.equal(categories.length,20);
  assert.equal(new Set(catalog.map(t=>t.label)).size,315);
  assert.equal(new Set(catalog.map(t=>t.theme)).size,315);
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
  assert.equal(search.filter(catalog,{gender:'girl',showAll:true}).length,315);
  assert.equal(search.filter(catalog,{gender:'boy',showAll:true}).length,315);
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


test('Marvel and DC are absent while anime inspirations keep the personalized child as the hero',()=>{
  for(const category of ['anime']){
    const rows=search.filter(catalog,{category,showAll:true});
    assert.equal(rows.length,52);
    assert.ok(rows.every(t=>t.theme.includes('Héros personnalisé')));
  }
  assert.equal(search.filter(catalog,{query:'Spider-Man',showAll:true}).length,0);
  assert.ok(!categories.some(c=>c.id==='comics'));
  assert.ok(!catalog.some(t=>t.category==='comics'));
  for(const name of ['Batman','Superman','Iron Man','Wonder Woman']) assert.equal(search.filter(catalog,{query:name,showAll:true}).length,0);
  assert.ok(search.filter(catalog,{query:'Naruto',showAll:true}).some(t=>t.category==='anime'));
  assert.ok(search.filter(catalog,{query:'ناروتو',showAll:true}).some(t=>t.category==='anime'));
});


test('displayed inspirations are separate from powers and visual descriptions sent to generation',()=>{
  const names=['Spider-Man','Iron Man','Thor','Hulk','Captain America','Doctor Strange','Black Panther','Ant-Man','Scarlet Witch','Superman','Batman','Wonder Woman','Flash','Aquaman','Green Lantern','Cyborg','Shazam','Supergirl','Zatanna','Goku','Naruto','Luffy','Tanjiro','Deku','Sailor Moon','Sacha','Pikachu','Sakura','Natsu','Edward Elric','Gon','Killua','Saitama','Ichigo','Yugi','Hinata','Tsubasa','Seiya','Astro Boy','Totoro','Sasuke','Vegeta','Gohan','Zoro','Nami','Nezuko','Zenitsu','Bakugo'];
  const profiles=catalog.filter(t=>['anime'].includes(t.category));
  assert.equal(profiles.length,52);
  assert.equal(new Set(profiles.map(t=>t.theme)).size,52);
  for(const profile of profiles){
    assert.ok(profile.theme.includes('Tenue et apparence :'));
    for(const name of names)assert.ok(!new RegExp('\\b'+name+'\\b','iu').test(profile.theme),profile.label+' leaked '+name);
  }
});


test('every inspiration includes a coherent world used by cover and story generation',()=>{
  const profiles=catalog.filter(t=>['anime'].includes(t.category));
  assert.equal(profiles.length,52);
  assert.ok(new Set(profiles.map(t=>t.world.setting)).size>=9);
  for(const profile of profiles){
    for(const key of ['setting','places','objects','mission']){
      assert.ok(profile.world[key].length>20);
      assert.ok(profile.theme.includes(profile.world[key]));
    }
    assert.ok(profile.theme.includes('dès la couverture'));
    assert.ok(profile.theme.includes('toute l’histoire'));
  }
  const village=profiles.find(t=>t.label.startsWith('Naruto'));
  assert.ok(village.world.places.includes('académie'));
});


test('all written references include clothing, equipment and opponents or appropriate obstacles',()=>{
  const profiles=catalog.filter(t=>['anime'].includes(t.category));
  for(const p of profiles){
    for(const key of ['costume','equipment','adversaries']){
      assert.ok(p.reference[key].length>40);
      assert.ok(p.theme.includes(p.reference[key]));
    }
    assert.ok(p.theme.includes('visage de l’enfant'));
    assert.ok(p.theme.includes('sans blessure ni scène sanglante'));
  }
  assert.ok(profiles.find(t=>t.label.startsWith('Tsubasa')).reference.adversaries.includes('pas de méchant'));
});


test('only the eight requested anime series remain, with ten characters in each priority series',()=>{
  const series=context.window.MLH_ANIME_SERIES;
  assert.equal(series.length,8);
  const expected=['dragon-ball','naruto','one-piece','demon-slayer','my-hero-academia','pokemon','hunter-x-hunter','captain-tsubasa'];
  assert.deepEqual(Array.from(series,g=>g.id),expected);
  const major=new Set(expected.slice(0,4));
  for(const group of series){
    const members=search.filter(catalog,{category:'anime',series:group.id,showAll:true});
    assert.equal(members.length,major.has(group.id)?10:3,group.label);
    assert.ok(members.every(t=>t.reference.costume&&t.world.setting&&t.seriesLabel===group.label));
    assert.equal(new Set(members.map(t=>t.reference.costume)).size,members.length);
  }
  const ninjas=search.filter(catalog,{category:'anime',series:'naruto',showAll:true});
  assert.ok(ninjas.some(t=>t.label.startsWith('Sasuke')));
  assert.ok(ninjas.some(t=>t.label.startsWith('Sakura Haruno')));
  assert.equal(new Set(ninjas.map(t=>t.world.setting)).size,1);
  const dragon=search.filter(catalog,{category:'anime',series:'dragon-ball',showAll:true});
  assert.ok(dragon.some(t=>t.label.startsWith('Vegeta')));
  assert.ok(dragon.some(t=>t.label.startsWith('Gohan')));
  assert.equal(search.filter(catalog,{query:'Naruto',showAll:true}).length,10);
  assert.equal(search.filter(catalog,{query:'ناروتو',showAll:true}).length,10);
});


test('removed series cannot appear in anime filters or search results',()=>{
  const removed=['sailor-moon','cardcaptor-sakura','fairy-tail','fullmetal-alchemist','one-punch-man','bleach','haikyu','saint-seiya','astro-boy','totoro'];
  for(const id of removed){
    assert.equal(search.filter(catalog,{category:'anime',series:id,showAll:true}).length,0);
  }
  for(const name of ['Sailor Moon','Totoro','Ichigo','Natsu']){
    assert.equal(search.filter(catalog,{category:'anime',query:name,showAll:true}).length,0,name);
  }
  for(const name of ['Piccolo','Trunks','Kakashi','Gaara','Sanji','Chopper','Rengoku','Shinobu']){
    assert.ok(search.filter(catalog,{category:'anime',query:name,showAll:true}).length>0,name);
  }
});

 test('Yu-Gi-Oh and its characters are absent from filters and search',()=>{
  assert.ok(!context.window.MLH_ANIME_SERIES.some(s=>s.id==='yu-gi-oh'));
  for(const query of ['Yu-Gi-Oh','Yugi','Seto Kaiba','Joey Wheeler']) assert.equal(search.filter(catalog,{query,showAll:true}).length,0,query);
 });


test('video game adventures are grouped in eight bilingual worlds and searchable without altering anime',()=>{
  const games=context.window.MLH_GAME_SERIES;
  assert.equal(games.length,8);
  const rows=search.filter(catalog,{category:'video-games',showAll:true});
  assert.equal(rows.length,24);
  for(const game of games){
    assert.ok(game.ar);
    const entries=search.filter(catalog,{category:'video-games',series:game.id,showAll:true});
    assert.equal(entries.length,3);
    assert.ok(entries.every(t=>t.seriesLabel===game.label&&t.ar&&t.world.mission&&t.reference.costume));
    assert.equal(search.filter(catalog,{query:game.label,category:'video-games',showAll:true}).length,3);
  }
  assert.equal(search.filter(catalog,{category:'anime',showAll:true}).length,52);
  assert.ok(rows.every(t=>t.theme.includes('référence initiale')&&t.theme.includes('couverture fixe sa tenue')));
});
