document.addEventListener("DOMContentLoaded",()=>{
const state={pack:1,price:69,name:"",age:"",language:"Français",photo:"",themes:[]};
const packNames={1:"Little Hero",2:"Super Hero",3:"Hero Gift"};
const prices={1:69,2:119,3:159};
const creation=document.getElementById("creation");
const cards=[...document.querySelectorAll(".wizard-card")];
const labels=[...document.querySelectorAll(".steps-labels span")];
const bar=document.getElementById("progressBar");
let step=1;
const maxThemes=()=>state.pack;
function render(){cards.forEach((c,i)=>c.hidden=i+1!==step);bar.style.width=(step*25)+"%";labels.forEach((x,i)=>x.classList.toggle("active",i+1===step));}
function openCreation(pack=1){state.pack=Number(pack);state.price=prices[state.pack];state.themes=[];document.querySelectorAll(".choice").forEach(x=>x.classList.toggle("selected",Number(x.dataset.wizardPack)===state.pack));creation.hidden=false;creation.scrollIntoView({behavior:"smooth",block:"start"});step=1;updateAdventureUI();render();}
document.querySelectorAll("[data-open-creation]").forEach(b=>b.addEventListener("click",()=>openCreation(state.pack)));
document.querySelectorAll("[data-pack]").forEach(b=>b.addEventListener("click",()=>openCreation(b.dataset.pack)));
document.querySelectorAll("[data-wizard-pack]").forEach(b=>b.addEventListener("click",()=>{state.pack=Number(b.dataset.wizardPack);state.price=prices[state.pack];state.themes=[];document.querySelectorAll(".choice").forEach(x=>x.classList.toggle("selected",x===b));updateAdventureUI();updatePreview();}));
const photoInput=document.getElementById("childPhoto");
photoInput.addEventListener("change",e=>{const file=e.target.files[0];if(!file)return;if(file.size>8*1024*1024){alert("La photo doit faire moins de 8 Mo.");photoInput.value="";return}const reader=new FileReader();reader.onload=()=>{state.photo=reader.result;document.getElementById("photoPreviewImg").src=state.photo;document.getElementById("photoPreview").hidden=false};reader.readAsDataURL(file);});
document.querySelectorAll(".theme-choice-grid button").forEach(b=>b.addEventListener("click",()=>{const theme=b.dataset.theme;if(state.themes.includes(theme)){state.themes=state.themes.filter(x=>x!==theme)}else{if(state.themes.length>=maxThemes()){alert("Votre pack contient "+maxThemes()+" aventure"+(maxThemes()>1?"s":"")+".");return}state.themes.push(theme)}document.querySelectorAll(".theme-choice-grid button").forEach(x=>x.classList.toggle("selected",state.themes.includes(x.dataset.theme)));updateAdventureUI();updatePreview();}));
function themeLabel(v){return v.replace(/^\s*[\p{Extended_Pictographic}\p{Emoji_Presentation}\uFE0F]+\s*/u,"").trim()}function updateAdventureUI(){const n=maxThemes();document.getElementById("themeInstruction").textContent="Choisissez exactement "+n+" aventure"+(n>1?"s":"")+".";document.getElementById("adventureSlots").innerHTML=Array.from({length:n},(_,i)=>'<span class="adventure-slot '+(state.themes[i]?"done":"")+'">Aventure '+(i+1)+(state.themes[i]?" · "+themeLabel(state.themes[i]):" · à choisir")+"</span>").join("");}
document.querySelectorAll(".next").forEach(b=>b.addEventListener("click",()=>{if(step===2){state.name=document.getElementById("childName").value.trim();state.age=document.getElementById("childAge").value;state.language=document.getElementById("language").value;if(!state.name||!state.age){alert("Veuillez renseigner le prénom et l'âge de votre enfant.");return}}if(step===3&&state.themes.length!==maxThemes()){alert("Choisissez exactement "+maxThemes()+" aventure"+(maxThemes()>1?"s":"")+" pour continuer.");return}if(step<4)step++;updatePreview();render();}));
document.querySelectorAll(".back").forEach(b=>b.addEventListener("click",()=>{if(step>1)step--;render();}));
function updatePreview(){document.getElementById("summaryName").textContent=state.name||"Votre enfant";document.getElementById("summaryAge").textContent=state.age||"—";document.getElementById("summaryLang").textContent=state.language;document.getElementById("summaryPack").textContent=packNames[state.pack];document.getElementById("summaryPrice").textContent=state.price+" DH";document.getElementById("previewTitle").textContent=state.name?state.name+" et ses aventures":"Mon aventure";document.getElementById("previewTheme").textContent=state.themes.length?state.themes.map(themeLabel).join(" · "):"Choisissez un univers";document.getElementById("summaryAdventures").innerHTML=state.themes.map((x,i)=>'<div><b>Aventure '+(i+1)+":</b> "+x+"</div>").join("");}
\nLa connexion WhatsApp sera activée avec le numéro My Little Hero avant la mise en ligne.");return}window.open("https://wa.me/"+phone+"?text="+encodeURIComponent(msg),"_blank");});
updateAdventureUI();updatePreview();render();
});
/* Bilingual site layer — preserves the existing visual design */
(function(){
  const T={
    "Comment ça marche":"كيف يعمل؟","Aventures":"المغامرات","Packs":"الباقات","FAQ":"الأسئلة الشائعة",
    "Créer son aventure":"أنشئ مغامرته","Créer mon aventure":"أنشئ مغامرتك","UNE HISTOIRE CRÉÉE RIEN QUE POUR LUI":"قصة صُنعت خصيصًا له","✨ UNE HISTOIRE CRÉÉE RIEN QUE POUR LUI":"قصة صُنعت خصيصًا له",
    "UNE AVENTURE RIEN QU'À LUI":"مغامرة صُنعت خصيصًا له","Votre enfant devient":"طفلك يصبح","le héros":"البطل",
    "de sa propre histoire.":"في قصته الخاصة.","À partir de son prénom, de son âge et de sa photo, nous imaginons une aventure originale qu'il pourra ensuite colorier et garder comme souvenir.":"انطلاقًا من اسمه وعمره وصورته، نصمم له مغامرة أصلية يمكنه تلوينها والاحتفاظ بها كذكرى.",
    "Une histoire personnalisée, inspirée de sa photo et de ses passions, puis transformée en aventure à colorier.":"قصة مخصصة مستوحاة من صورته واهتماماته، ثم تتحول إلى مغامرة يمكنه تلوينها.",
    "Créer son livre":"أنشئ كتابه","Créer son aventure":"أنشئ مغامرته","Découvrir le concept ↓":"اكتشف الفكرة ↓",
    "Personnalisé":"مخصص","Dès 69 DH":"ابتداءً من 69 درهم","À partir de 69 DH":"ابتداءً من 69 درهم","Digital ou imprimé":"رقمي أو مطبوع",
    "À colorier":"للتلوين","10 pages par aventure":"10 صفحات لكل مغامرة","aventures possibles":"مغامرات ممكنة",
    "univers possibles":"عوالم ممكنة","pages par aventure":"صفحات لكل مغامرة","packs au choix":"باقات للاختيار",
    "créé avec soin":"مصمم بعناية","COMMENT ÇA MARCHE":"كيف يعمل؟","Simple pour vous.":"بسيط بالنسبة لكم.","Magique pour lui.":"ساحر بالنسبة له.",
    "Quelques choix suffisent pour lancer la création de son aventure.":"بضعة اختيارات تكفي لبدء إنشاء مغامرته.",
    "En quelques étapes, nous créons une aventure unique à son image.":"في بضع خطوات، نصمم مغامرة فريدة تشبهه.",
    "Son prénom & sa photo":"اسمه وصورته","Indiquez les informations de votre petit héros et ajoutez sa photo.":"أدخل معلومات بطلك الصغير وأضف صورته.",
    "Vous nous donnez les informations de votre petit héros.":"أخبرنا بمعلومات بطلك الصغير.",
    "Son univers":"عالمه","Choisissez parmi nos aventures : magie, espace, dinosaures, sport et bien plus.":"اختر من بين مغامراتنا: السحر والفضاء والديناصورات والرياضة وغيرها.",
    "Choisissez son univers : espace, dinosaures, magie, football et plus.":"اختر عالمه: الفضاء والديناصورات والسحر وكرة القدم وغيرها.",
    "Nous créons son livre":"نصمم كتابه","Son personnage devient le héros d'une histoire originale et illustrée.":"تتحول شخصيته إلى بطل قصة أصلية ومصورة.",
    "Il devient l'artiste":"يصبح هو الفنان","Il découvre son aventure et donne vie aux pages en les coloriant.":"يكتشف مغامرته ويمنح الصفحات حياة من خلال تلوينها.",
    "Il donne vie à l'histoire":"يمنح القصة حياة","Il reçoit son aventure et peut colorier chaque page.":"يتلقى مغامرته ويمكنه تلوين كل صفحة.",
    "CHOISIS SON UNIVERS":"اختر عالمه","Une aventure pour":"مغامرة لكل","chaque imagination":"خيال","chaque enfant":"طفل",
    "Des mondes très différents pour que chaque enfant trouve son aventure.":"عوالم متنوعة جدًا ليجد كل طفل مغامرته.",
    "Et si son imagination choisissait la prochaine mission ?":"ماذا لو اختار خياله المهمة القادمة؟",
    "Et ce n'est qu'un aperçu.":"وهذا مجرد جزء من الخيارات.","Plus de 30 univers sont disponibles pendant la création.":"أكثر من 30 عالمًا متاح أثناء الإنشاء.",
    "Plus de 30 univers possibles":"أكثر من 30 عالمًا ممكنًا","Le choix complet sera disponible pendant la création.":"ستتوفر جميع الاختيارات أثناء الإنشاء.",
    "NOS 3 EXPÉRIENCES":"تجاربنا الثلاث","NOS PACKS":"باقاتنا","Choisissez son":"اختر","niveau d'aventure":"مستوى المغامرة",
    "Une première aventure, une collection de deux mondes ou le cadeau complet.":"مغامرة أولى، أو مجموعة من عالمين، أو الهدية الكاملة.",
    "Une aventure, plusieurs aventures, ou le cadeau qui fait vraiment plaisir.":"مغامرة واحدة، عدة مغامرات، أو الهدية المثالية.",
    "POUR COMMENCER":"للبدء","LE PLUS CHOISI":"الأكثر اختيارًا","LE CADEAU":"الهدية",
    "01 AVENTURE":"01 مغامرة","02 AVENTURES":"02 مغامرتان","03 AVENTURES":"03 مغامرات",
    "Son premier livre personnalisé.":"كتابه الشخصي الأول.","Deux univers pour prolonger le plaisir.":"عالمان لمزيد من المتعة.","La collection complète à offrir.":"المجموعة الكاملة كهدية.",
    "digital":"رقمي","Digital":"رقمي","Imprimé":"مطبوع","Digital + imprimé":"رقمي + مطبوع",
    "1 aventure de 10 pages":"مغامرة واحدة من 10 صفحات","2 aventures de 10 pages":"مغامرتان من 10 صفحات","3 aventures de 10 pages":"3 مغامرات من 10 صفحات",
    "Son personnage personnalisé":"شخصيته مخصصة","Deux univers au choix":"عالمان للاختيار","Deux livres personnalisés":"كتابان مخصصان",
    "Trois univers au choix":"ثلاثة عوالم للاختيار","Trois livres personnalisés":"ثلاثة كتب مخصصة","Illustrations à colorier":"رسومات للتلوين",
    "Le format imprimé et le format Digital + Imprimé sont finalisés avec notre équipe lors de la commande.":"يتم تأكيد النسخة المطبوعة ونسخة رقمي + مطبوع مع فريقنا عند الطلب.",
    "Imprimé et Digital + Imprimé disponibles lors de la commande.":"النسخة المطبوعة ونسخة رقمي + مطبوع متاحتان عند الطلب.",
    "PLUS QU'UN COLORIAGE":"أكثر من مجرد تلوين","Un souvenir qu'il pourra":"ذكرى يمكنه","garder longtemps.":"الاحتفاظ بها طويلًا.",
    "Son prénom. Son visage. Son imagination. Son histoire. Une création pensée pour lui, et un moment de complicité à partager.":"اسمه. وجهه. خياله. قصته. إبداع صُمم من أجله، ولحظة جميلة تشاركونها معًا.",
    "Créer son histoire →":"أنشئ قصته →","Dans cette histoire, c'est moi le héros !":"في هذه القصة، أنا البطل!","— votre petit héros":"— بطلكم الصغير",
    "CRÉEZ SON AVENTURE":"أنشئ مغامرته","Construisons son livre":"لنبنِ كتابه","ensemble.":"معًا.","Vous choisissez. Nous créons. Il s'évade.":"أنتم تختارون. نحن نصمم. وهو ينطلق في المغامرة.",
    "1. Pack":"1. الباقة","2. Héros":"2. البطل","3. Aventure":"3. المغامرة","4. Aperçu":"4. المعاينة",
    "ÉTAPE 1 SUR 4":"الخطوة 1 من 4","ÉTAPE 2 SUR 4":"الخطوة 2 من 4","ÉTAPE 3 SUR 4":"الخطوة 3 من 4","ÉTAPE 4 SUR 4":"الخطوة 4 من 4",
    "Choisissez son expérience":"اختر تجربته","Choisissez votre pack":"اختر باقتك","Le prix affiché ici correspond au format digital.":"السعر المعروض هنا يخص النسخة الرقمية.",
    "Vous pourrez modifier votre choix à tout moment.":"يمكنك تعديل اختيارك في أي وقت.",
    "Continuer →":"متابعة →","Retour":"رجوع","Modifier":"تعديل","Voir mon aperçu →":"عرض المعاينة →",
    "Parlez-nous de son héros":"حدثنا عن بطلك","Ces informations servent à personnaliser son aventure.":"تُستخدم هذه المعلومات لتخصيص مغامرته.",
    "Prénom":"الاسم","Âge":"العمر","Choisir":"اختيار","Langue":"اللغة","Photo de l'enfant":"صورة الطفل","Photo sélectionnée ✓":"تم اختيار الصورة ✓",
    "Elle servira à créer son personnage.":"ستُستخدم لإنشاء شخصيته.","Quelle sera sa mission ?":"ما مهمته؟","Choisissez 1 aventure.":"اختر مغامرة واحدة.",
    "Choisissez exactement 1 aventure pour continuer.":"اختر مغامرة واحدة بالضبط للمتابعة.","Choisissez exactement":"اختر بالضبط",
    "Son aventure est prête à être créée":"مغامرته جاهزة للإنشاء","Vérifiez les informations avant de valider.":"تحقق من المعلومات قبل التأكيد.",
    "Mon aventure":"مغامرتي","Choisissez un univers":"اختر عالمًا","Héros":"البطل","Pack":"الباقة","Total estimé":"المجموع التقديري",
    "Vos informations et la photo de votre enfant sont utilisées uniquement pour préparer sa commande.":"تُستخدم معلوماتك وصورة طفلك فقط لإعداد طلبه.",
    "Valider ma commande":"تأكيد طلبي","Valider ma commande sur WhatsApp":"تأكيد طلبي عبر واتساب","La validation finale se fera avec notre équipe sur WhatsApp.":"سيتم تأكيد الطلب النهائي مع فريقنا عبر واتساب.",
    "Créer":"إنشاء","Tous droits réservés":"جميع الحقوق محفوظة",
    "Monde magique":"العالم السحري","Fées":"الجنيات","Licorne":"اليونيكورن","Royaume":"المملكة","Dragon":"التنين","Pirates":"القراصنة","Trésor":"الكنز","Espace":"الفضاء","Robots":"الروبوتات","Dinosaures":"الديناصورات","Sous-marin":"العالم تحت الماء","Sirènes":"حوريات البحر","Forêt":"الغابة","Safari":"السفاري","Sauvetage":"إنقاذ الحيوانات","Football":"كرة القدم","Basket":"كرة السلة","Course":"السباق","Détective":"المحقق","Mission secrète":"مهمة سرية","Chevalier":"الفارس","Art":"الفن","Musique":"الموسيقى","Danse":"الرقص","Pâtisserie":"الحلويات","Mode":"الأزياء","Science":"العلوم","Temps":"السفر عبر الزمن","Mon propre thème":"موضوعي الخاص",
    "1 aventure · dès 69 DH":"مغامرة واحدة · ابتداءً من 69 درهم","2 aventures · dès 119 DH":"مغامرتان · ابتداءً من 119 درهم","3 aventures · dès 159 DH":"3 مغامرات · ابتداءً من 159 درهم",
    "1 aventure · 69 DH":"مغامرة واحدة · 69 درهم","2 aventures · 119 DH":"مغامرتان · 119 درهم","3 aventures · 159 DH":"3 مغامرات · 159 درهم"
  };
  const themeAr={"Monde magique":"العالم السحري","Fées":"الجنيات","Licorne":"اليونيكورن","Royaume":"المملكة","Dragon":"التنين","Pirates":"القراصنة","Trésor":"الكنز","Espace":"الفضاء","Robots":"الروبوتات","Dinosaures":"الديناصورات","Sous-marin":"العالم تحت الماء","Sirènes":"حوريات البحر","Forêt":"الغابة","Safari":"السفاري","Sauvetage":"إنقاذ الحيوانات","Football":"كرة القدم","Basket":"كرة السلة","Course":"السباق","Détective":"المحقق","Mission secrète":"مهمة سرية","Chevalier":"الفارس","Art":"الفن","Musique":"الموسيقى","Danse":"الرقص","Pâtisserie":"الحلويات","Mode":"الأزياء","Science":"العلوم","Temps":"السفر عبر الزمن","Mon propre thème":"موضوعي الخاص"};
  const originals=new WeakMap();
  function norm(s){return s.replace(/\s+/g," ").trim()}
  function translate(lang){
    const ar=lang==="ar";
    document.documentElement.lang=ar?"ar":"fr";
    document.body.dir=ar?"rtl":"ltr";
    document.body.classList.toggle("site-ar",ar);
    document.title=ar?"My Little Hero — طفلك يصبح بطل قصته":"My Little Hero — Ton enfant devient le héros";
    document.querySelector('meta[name="description"]')?.setAttribute("content",ar?"My Little Hero — قصص مخصصة يصبح فيها كل طفل بطل قصته الخاصة.":"My Little Hero — des histoires personnalisées où chaque enfant devient le héros de sa propre aventure.");
    const heroTitle=document.querySelector(".hero-copy h1");
    if(heroTitle){
      if(ar){
        heroTitle.classList.add("ar-title");
        heroTitle.innerHTML="طفلك يصبح <span class=\"ar-word purple\">البطل</span> في قصته الخاصة.";
      }else{
        heroTitle.classList.remove("ar-title");
        heroTitle.innerHTML="Votre enfant devient <span>le héros</span> de sa propre histoire.";
      }
    }
    const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
    const nodes=[]; while(walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach(n=>{
      if(!originals.has(n)) originals.set(n,n.nodeValue);
      const base=norm(originals.get(n)||"");
      if(!base)return;
      n.nodeValue=ar?(T[base]||base):(base);
    });
    document.querySelectorAll("[data-theme-label]").forEach(b=>{
      const label=b.dataset.themeLabel;
      const s=b.querySelector("span:last-child");
      if(s)s.textContent=ar?(themeAr[label]||label):label;
    });
    const langSel=document.getElementById("language");
    if(langSel){
      [...langSel.options].forEach(o=>{ if(o.value==="Français"||o.textContent==="Français")o.textContent=ar?"الفرنسية":"Français"; if(o.value==="العربية"||o.textContent==="العربية")o.textContent="العربية";});
    }
    const toggle=document.getElementById("siteLanguageToggle");
    if(toggle){toggle.querySelector("[data-lang='fr']").classList.toggle("active",!ar);toggle.querySelector("[data-lang='ar']").classList.toggle("active",ar);}
    localStorage.setItem("mlh-site-language",ar?"ar":"fr");
  }
  function addToggle(){
    const header=document.querySelector(".site-header"); if(!header||document.getElementById("siteLanguageToggle"))return;
    const el=document.createElement("div");el.id="siteLanguageToggle";el.innerHTML='<button type="button" data-lang="fr">FR</button><span></span><button type="button" data-lang="ar">العربية</button>';
    el.querySelector("[data-lang='fr']").onclick=()=>translate("fr");el.querySelector("[data-lang='ar']").onclick=()=>translate("ar");
    header.insertBefore(el,header.querySelector(".nav-cta"));
  }
  function injectStyle(){
    if(document.getElementById("mlh-i18n-style"))return;
    const s=document.createElement("style");s.id="mlh-i18n-style";s.textContent=`
      #siteLanguageToggle{display:flex;align-items:center;gap:8px;margin-left:auto;margin-right:12px;padding:5px 8px;border:1px solid rgba(91,75,219,.14);border-radius:999px;background:rgba(255,255,255,.88);box-shadow:0 5px 16px rgba(48,43,82,.05)}
      #siteLanguageToggle button{border:0;background:transparent;padding:4px 7px;border-radius:999px;font:800 10px Nunito;cursor:pointer;color:#77738a}
      #siteLanguageToggle button.active{background:#5b4bdb;color:#fff}
      #siteLanguageToggle span{width:1px;height:14px;background:#ddd9ea}
      body.site-ar{direction:rtl}
      body.site-ar .site-header nav,body.site-ar .hero-actions,body.site-ar .trust-row,body.site-ar .wizard-actions{direction:rtl}
      body.site-ar .hero-copy,body.site-ar .section-heading,body.site-ar .creation-heading,body.site-ar .wizard-card,body.site-ar .price-card,body.site-ar .faq-grid,body.site-ar footer{text-align:right}
      body.site-ar .choice{text-align:right}
      body.site-ar .price-options span{flex-direction:row-reverse}
      body.site-ar .footer-links{justify-content:flex-start}
      body.site-ar .form-grid input,body.site-ar .form-grid select{direction:rtl}
      body.site-ar .brand-logo{direction:ltr}
      @media(max-width:900px){#siteLanguageToggle{margin-left:0;margin-right:8px}}
      @media(max-width:600px){#siteLanguageToggle{margin-right:auto}#siteLanguageToggle button{padding:3px 6px}}
    `;document.head.appendChild(s);
  }
  function bind(){
    addToggle();injectStyle();
    const saved=localStorage.getItem("mlh-site-language")||"fr";translate(saved);
    const obs=new MutationObserver(()=>{ if(!document.body.dataset.mlhTranslating){document.body.dataset.mlhTranslating="1";requestAnimationFrame(()=>{translate(localStorage.getItem("mlh-site-language")||"fr");delete document.body.dataset.mlhTranslating})}});
    obs.observe(document.body,{childList:true,subtree:true});
    const order=document.getElementById("orderButton");
    if(order)order.addEventListener("click",e=>{
      if(localStorage.getItem("mlh-site-language")!=="ar")return;
      e.preventDefault();e.stopImmediatePropagation();
      const g=id=>document.getElementById(id)?.textContent?.trim()||"";
      const themes=[...document.querySelectorAll("#summaryAdventures div")].map(x=>x.textContent.replace(/^Aventure\s*\d+\s*:\s*/,"").trim()).map(x=>themeAr[x]||x);
      const msg="مرحبًا My Little Hero\nأرغب في طلب مغامرة مخصصة لطفلي.\n\nالبطل: "+(g("summaryName")||"يحدد لاحقًا")+"\nالعمر: "+(g("summaryAge")||"يحدد لاحقًا")+"\nاللغة: العربية\nالباقة: "+g("summaryPack")+"\nالمغامرات: "+(themes.join("، ")||"تحدد لاحقًا")+"\nالسعر الرقمي: "+g("summaryPrice")+"\n\nأرغب في تأكيد طلبي.";
      window.open("https://wa.me/212603983800?text="+encodeURIComponent(msg),"_blank");
    },true);
  }
  if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",bind);else bind();
})();
/* Arabic dynamic UI helpers */
(function(){
  const themeAr={"Monde magique":"العالم السحري","Fées":"الجنيات","Licorne":"اليونيكورن","Royaume":"المملكة","Dragon":"التنين","Pirates":"القراصنة","Trésor":"الكنز","Espace":"الفضاء","Robots":"الروبوتات","Dinosaures":"الديناصورات","Sous-marin":"العالم تحت الماء","Sirènes":"حوريات البحر","Forêt":"الغابة","Safari":"السفاري","Sauvetage":"إنقاذ الحيوانات","Football":"كرة القدم","Basket":"كرة السلة","Course":"السباق","Détective":"المحقق","Mission secrète":"مهمة سرية","Chevalier":"الفارس","Art":"الفن","Musique":"الموسيقى","Danse":"الرقص","Pâtisserie":"الحلويات","Mode":"الأزياء","Science":"العلوم","Temps":"السفر عبر الزمن","Mon propre thème":"موضوعي الخاص"};
  const apply=()=>{
    if(localStorage.getItem("mlh-site-language")!=="ar")return;
    const n=document.querySelectorAll(".adventure-slot").length||1;
    const instr=document.getElementById("themeInstruction");
    if(instr)instr.textContent="اختر بالضبط "+n+" "+(n>1?"مغامرات":"مغامرة")+" للمتابعة.";
    document.querySelectorAll(".adventure-slot").forEach((el,i)=>{
      const done=el.classList.contains("done");
      const txt=done?(el.textContent.split("·")[1]||"").trim():"للاختيار";
      const base=Object.keys(themeAr).find(k=>txt.includes(k))||txt;
      el.textContent="المغامرة "+(i+1)+" · "+(themeAr[base]||"للاختيار");
    });
    document.querySelectorAll("#summaryAdventures div").forEach((el,i)=>{
      const raw=el.textContent.replace(/^Aventure\s*\d+\s*:\s*/,"").trim();
      el.innerHTML="<b>المغامرة "+(i+1)+":</b> "+(themeAr[raw]||raw);
    });
  };
  const oldAlert=window.alert;
  window.alert=function(msg){
    if(localStorage.getItem("mlh-site-language")!=="ar")return oldAlert(msg);
    let m=String(msg);
    m=m.replace("Veuillez renseigner le prénom et l'âge de votre enfant.","يرجى إدخال اسم طفلك وعمره.")
      .replace(/Votre pack contient (\d+) aventure(s)? \.?/,"الباقة تحتوي على $1 "+(RegExp.$1>1?"مغامرات":"مغامرة")+" .")
      .replace(/Choisissez exactement (\d+) aventure(s)? pour continuer\./,"اختر بالضبط $1 "+(RegExp.$1>1?"مغامرات":"مغامرة")+" للمتابعة.")
      .replace("La photo doit faire moins de 8 Mo.","يجب ألا يتجاوز حجم الصورة 8 ميغابايت.");
    return oldAlert(m);
  };
  new MutationObserver(()=>requestAnimationFrame(apply)).observe(document.body,{childList:true,subtree:true});
  setInterval(apply,700);
  apply();
})();
// Arabic text normalization and spacing
(function(){
 const A={
 "اختر":"اختر","اختر مغامرة واحدة.":"اختر مغامرة واحدة.","اختر بالضبط":"اختر بالضبط",
 "المغامرة":"المغامرة","مغامرة":"مغامرة","مغامرات":"مغامرات",
 "ابتداءً من 69 درهم":"ابتداءً من 69 درهمًا","ابتداءً من 119 درهم":"ابتداءً من 119 درهمًا","ابتداءً من 159 درهم":"ابتداءً من 159 درهمًا",
 "العالم السحري":"العالم السحري","المملكة":"المملكة","اليونيكورن":"اليونيكورن","القراصنة":"القراصنة",
 "الديناصورات":"الديناصورات","الفضاء":"الفضاء","الروبوتات":"الروبوتات","كرة القدم":"كرة القدم",
 "المحقق":"المحقق","الفارس":"الفارس","العلوم":"العلوم","الحلويات":"الحلويات"
 };
 function clean(s){return s.replace(/[ ]{2,}/g," ").replace(/\s+([،.!؟:؛])/g,"$1").replace(/([،.!؟:؛])(?=[^\s])/g,"$1 ");}
 function run(){
   if(localStorage.getItem("mlh-site-language")!=="ar")return;
   const w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
   while(w.nextNode()){const n=w.currentNode;if(n.nodeValue&&/[\u0600-\u06FF]/.test(n.nodeValue))n.nodeValue=clean(n.nodeValue);}
 }
 setInterval(run,500); run();
})();