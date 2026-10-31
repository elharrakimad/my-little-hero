// Search is shared by the UI and tests; it never changes the selected adventures.
(function(){
  const normalize=value=>String(value||"").normalize("NFD").replace(/\p{M}/gu,"").toLocaleLowerCase().replace(/[’']/g," ");
  window.MLHThemeSearch={
    filter(catalog,{query="",category="all",gender="",showAll=false}={}){
      const words=normalize(query).split(/\s+/).filter(Boolean);
      const categories=new Map((window.MLH_THEME_CATEGORIES||[]).map(c=>[c.id,c]));
      return catalog.filter(theme=>{
        if(category!=="all"&&theme.category!==category)return false;
        if(!showAll&&gender&&theme.profile&&theme.profile!==gender)return false;
        const group=categories.get(theme.category)||{};
        const text=normalize([theme.label,theme.ar,theme.theme,group.label,group.ar].join(" "));
        return words.every(word=>text.includes(word));
      });
    }
  };
})();

document.addEventListener("DOMContentLoaded",()=>{
  const gender=document.getElementById("childGender"), grid=document.querySelector(".theme-choice-grid");
  const catalog=window.MLH_THEME_CATALOG, categories=window.MLH_THEME_CATEGORIES;
  const search=document.getElementById("themeSearch"), category=document.getElementById("themeCategory");
  const toggle=document.getElementById("themeScope"), result=document.getElementById("themeResults");
  const empty=document.getElementById("themeEmpty"), reset=document.getElementById("themeReset");
  if(!gender||!grid||!catalog||!categories||!search||!category||!toggle)return;
  let showAll=false;
  const options=[];
  for(const group of categories){
    const option=document.createElement("option");option.value=group.id;option.textContent=group.label;
    category.append(option);options.push({option,group});
  }
  function buttonFor(theme){
    const button=document.createElement("button");button.type="button";
    button.dataset.theme=theme.theme;button.dataset.themeLabel=theme.label;
    const icon=document.createElement("span");icon.className="theme-icon";icon.setAttribute("aria-hidden","true");icon.textContent=theme.icon;
    const label=document.createElement("span");label.textContent=theme.label;
    button.append(icon,label);return {button,label,theme};
  }
  const custom=buttonFor({theme:"✨ Mon propre thème",label:"Mon propre thème",ar:"موضوعي الخاص",icon:"✨"});
  const customGroup=document.createElement("div");customGroup.className="theme-custom-choice";customGroup.append(custom.button);
  grid.replaceChildren(customGroup);
  const groups=categories.map(group=>{
    const details=document.createElement("details");details.className="theme-category-group";details.dataset.category=group.id;
    const summary=document.createElement("summary");
    const title=document.createElement("span"),count=document.createElement("span");count.className="theme-category-count";
    summary.append(title,count);
    const cards=document.createElement("div");cards.className="theme-group-grid";
    const entries=catalog.filter(t=>t.category===group.id).map(buttonFor);
    entries.forEach(entry=>cards.append(entry.button));
    details.append(summary,cards);grid.append(details);
    return {details,title,count,group,entries};
  });
  function render(resetOpen=false){
    const ar=document.documentElement.lang==="ar";
    const matches=new Set(window.MLHThemeSearch.filter(catalog,{query:search.value,category:category.value,gender:gender.value,showAll}));
    search.placeholder=ar?"مثال: تنين، كرة القدم، طبيب بيطري…":"Ex. dragon, football, vétérinaire…";
    category.options[0].textContent=ar?"كل الفئات":"Toutes les catégories";
    options.forEach(({option,group})=>option.textContent=ar?group.ar:group.label);
    toggle.textContent=showAll?(ar?"العودة إلى الاقتراحات":"Revenir aux suggestions"):(ar?`عرض جميع المواضيع (${catalog.length})`:`Voir tous les thèmes (${catalog.length})`);
    toggle.setAttribute("aria-pressed",String(showAll));
    custom.label.textContent=ar?custom.theme.ar:custom.theme.label;
    for(const item of groups){
      let count=0;
      for(const entry of item.entries){
        entry.button.hidden=!matches.has(entry.theme);
        entry.label.textContent=ar?entry.theme.ar:entry.theme.label;
        if(!entry.button.hidden)count++;
      }
      item.details.hidden=count===0;
      item.title.textContent=`${item.group.icon} ${ar?item.group.ar:item.group.label}`;
      item.count.textContent=ar?`${count} موضوع`:`${count} ${count===1?"thème":"thèmes"}`;
      if(resetOpen)item.details.open=!!search.value.trim()||category.value!=="all";
    }
    result.textContent=ar?`${matches.size} موضوع · اختر فئة أو ابحث عن مغامرة. الخاص بك متاح دائمًا.`:`${matches.size} ${matches.size===1?"thème":"thèmes"} · Ouvrez une catégorie ou recherchez une aventure. Votre propre thème reste disponible.`;
    empty.hidden=matches.size!==0;
    reset.hidden=!search.value&&category.value==="all"&&!showAll;
    reset.textContent=ar?"مسح الفلاتر":"Effacer les filtres";
  }
  search.addEventListener("input",()=>{if(search.value.trim())showAll=true;render(true);});
  category.addEventListener("change",()=>{if(category.value!=="all")showAll=true;render(true);});
  toggle.addEventListener("click",()=>{showAll=!showAll;if(!showAll){search.value="";category.value="all";}render(true);});
  reset.addEventListener("click",()=>{search.value="";category.value="all";showAll=false;render(true);});
  gender.addEventListener("change",()=>{search.value="";category.value="all";showAll=false;render(true);});
  new MutationObserver(()=>render()).observe(document.documentElement,{attributes:true,attributeFilter:["lang"]});
  render();
});
