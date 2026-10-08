document.addEventListener("DOMContentLoaded",()=>{const state={pack:1,price:69,name:"",age:"",language:"Français",photo:"",themes:[]};const packNames={1:"Little Hero",2:"Super Hero",3:"Hero Gift"};const prices={1:69,2:119,3:159};const phone="212603983800";const creation=document.getElementById("creation");const cards=[...document.querySelectorAll(".wizard-card")];const labels=[...document.querySelectorAll(".steps-labels span")];const bar=document.getElementById("progressBar");let step=1;const maxThemes=()=>state.pack;function render(){cards.forEach((c,i)=>c.hidden=i+1!==step);bar.style.width=(step*25)+"%";labels.forEach((x,i)=>x.classList.toggle("active",i+1===step))}function openCreation(pack=1){state.pack=Number(pack);state.price=prices[state.pack];state.themes=[];document.querySelectorAll(".choice").forEach(x=>x.classList.toggle("selected",Number(x.dataset.wizardPack)===state.pack));creation.hidden=false;creation.scrollIntoView({behavior:"smooth",block:"start"});step=1;updateAdventureUI();updatePreview();render()}document.querySelectorAll("[data-open-creation]").forEach(b=>b.addEventListener("click",()=>openCreation(state.pack)));document.querySelectorAll("[data-pack]").forEach(b=>b.addEventListener("click",()=>openCreation(b.dataset.pack)));document.querySelectorAll("[data-wizard-pack]").forEach(b=>b.addEventListener("click",()=>{state.pack=Number(b.dataset.wizardPack);state.price=prices[state.pack];state.themes=[];document.querySelectorAll(".choice").forEach(x=>x.classList.toggle("selected",x===b));updateAdventureUI();updatePreview()}));const photoInput=document.getElementById("childPhoto");photoInput.addEventListener("change",e=>{const file=e.target.files[0];if(!file)return;if(file.size>8*1024*1024){alert("La photo doit faire moins de 8 Mo.");photoInput.value="";return}const reader=new FileReader();reader.onload=()=>{state.photo=reader.result;document.getElementById("photoPreviewImg").src=state.photo;document.getElementById("photoPreview").hidden=false};reader.readAsDataURL(file)});document.querySelectorAll(".theme-choice-grid button").forEach(b=>b.addEventListener("click",()=>{const theme=b.dataset.theme;if(state.themes.includes(theme)){state.themes=state.themes.filter(x=>x!==theme)}else{if(state.themes.length>=maxThemes()){alert("Votre pack contient "+maxThemes()+" aventure"+(maxThemes()>1?"s":"")+" .");return}state.themes.push(theme)}document.querySelectorAll(".theme-choice-grid button").forEach(x=>x.classList.toggle("selected",state.themes.includes(x.dataset.theme)));updateAdventureUI();updatePreview()}));function themeLabel(v){return v.replace(/^\s*[\p{Extended_Pictographic}\p{Emoji_Presentation}\uFE0F]+\s*/u,"").trim()}function updateAdventureUI(){const n=maxThemes();document.getElementById("themeInstruction").textContent="Choisissez exactement "+n+" aventure"+(n>1?"s":"")+".";document.getElementById("adventureSlots").innerHTML=Array.from({length:n},(_,i)=>'<span class="adventure-slot '+(state.themes[i]?"done":"")+'">Aventure '+(i+1)+(state.themes[i]?" · "+themeLabel(state.themes[i]):" · à choisir")+"</span>").join("")}document.querySelectorAll(".next").forEach(b=>b.addEventListener("click",()=>{if(step===2){state.name=document.getElementById("childName").value.trim();state.age=document.getElementById("childAge").value;state.language=document.getElementById("language").value;if(!state.name||!state.age){alert("Veuillez renseigner le prénom et l'âge de votre enfant.");return}}if(step===3&&state.themes.length!==maxThemes()){alert("Choisissez exactement "+maxThemes()+" aventure"+(maxThemes()>1?"s":"")+" pour continuer.");return}if(step<4)step++;updatePreview();render()}));document.querySelectorAll(".back").forEach(b=>b.addEventListener("click",()=>{if(step>1)step--;render()}));function updatePreview(){document.getElementById("summaryName").textContent=state.name||"Votre enfant";document.getElementById("summaryAge").textContent=state.age||"—";document.getElementById("summaryLang").textContent=state.language;document.getElementById("summaryPack").textContent=packNames[state.pack];document.getElementById("summaryPrice").textContent=state.price+" DH";document.getElementById("previewTitle").textContent=state.name?state.name+" et ses aventures":"Mon aventure";document.getElementById("previewTheme").textContent=state.themes.length?state.themes.map(themeLabel).join(" · "):"Choisissez un univers";document.getElementById("summaryAdventures").innerHTML=state.themes.map((x,i)=>"<div><b>Aventure "+(i+1)+":</b> "+x+"</div>").join("")}document.getElementById("orderButton").addEventListener("click",()=>{const msg="Bonjour My Little Hero\nJe souhaite commander une aventure personnalisée.\n\nHéros : "+(state.name||"À préciser")+"\nÂge : "+(state.age||"À préciser")+"\nLangue : "+state.language+"\nPack : "+packNames[state.pack]+"\nAventures : "+(state.themes.map(themeLabel).join(", ")||"À choisir")+"\nPrix digital : "+state.price+" DH\nPhoto : je l'enverrai dans cette conversation WhatsApp.\n\nJe souhaite valider ma commande.";window.open("https://wa.me/"+phone+"?text="+encodeURIComponent(msg),"_blank")});updateAdventureUI();updatePreview();render()});
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

(function(){
  const originals=new WeakMap();
  let translating=false;
  const norm=s=>String(s||"").replace(/\s+/g," ").trim();
  const applyHeadings=(ar)=>{
    const h=document.querySelector(".hero-copy h1");
    if(h){h.classList.toggle("ar-spaced-heading",ar);h.innerHTML=ar?'طفلك يصبح <span class="purple">البطل</span> في قصته الخاصة.':'Votre enfant devient <span>le héros</span> de sa propre histoire.';}
    const a=document.querySelector("#adventures .section-heading h2");
    if(a){a.classList.toggle("ar-spaced-heading",ar);a.innerHTML=ar?'مغامرة لكل <span class="purple">خيال</span>':'Une aventure pour <span>chaque imagination</span>';}
    const e=document.querySelector(".emotional-card h2");
    if(e){e.classList.toggle("ar-spaced-heading",ar);e.innerHTML=ar?'ذكرى يمكنه الاحتفاظ بها <span class="purple">طويلًا.</span>':"Un souvenir qu'il pourra <span>garder longtemps.</span>";}
    const c=document.querySelector(".creation-heading h2");
    if(c){c.classList.toggle("ar-spaced-heading",ar);c.innerHTML=ar?'لنبنِ كتابه <span class="purple">معًا.</span>':'Construisons son livre <span>ensemble.</span>';}
  };
  function translate(lang){
    if(translating)return;
    translating=true;
    const ar=lang==="ar";
    document.documentElement.lang=ar?"ar":"fr";
    document.body.dir=ar?"rtl":"ltr";
    document.body.classList.toggle("site-ar",ar);
    localStorage.setItem("mlh-site-language",ar?"ar":"fr");
    document.title=ar?"My Little Hero — طفلك يصبح بطل قصته":"My Little Hero — Ton enfant devient le héros";
    const meta=document.querySelector('meta[name="description"]');
    if(meta)meta.content=ar?"My Little Hero — قصص مخصصة يصبح فيها كل طفل بطل قصته الخاصة.":"My Little Hero — des histoires personnalisées où chaque enfant devient le héros de sa propre aventure.";
    const w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
    const nodes=[];while(w.nextNode())nodes.push(w.currentNode);
    nodes.forEach(n=>{
      if(!originals.has(n))originals.set(n,n.nodeValue);
      const base=norm(originals.get(n));
      if(base)n.nodeValue=ar?(T[base]||base):base;
    });
    applyHeadings(ar);
    document.querySelectorAll("[data-theme-label]").forEach(b=>{
      const label=b.dataset.themeLabel,s=b.querySelector("span:last-child");
      if(s)s.textContent=ar?(themeAr[label]||label):label;
    });
    const toggle=document.getElementById("siteLanguageToggle");
    if(toggle){
      const fr=toggle.querySelector("[data-lang='fr']"),a=toggle.querySelector("[data-lang='ar']");
      if(fr)fr.classList.toggle("active",!ar);if(a)a.classList.toggle("active",ar);
    }
    translating=false;
  }
  window.setMyLittleHeroLanguage=translate;
  function setup(){
    let el=document.getElementById("siteLanguageToggle");
    if(!el){
      const header=document.querySelector(".site-header");
      if(header){
        el=document.createElement("div");el.id="siteLanguageToggle";
        el.innerHTML='<button type="button" data-lang="fr">FR</button><span></span><button type="button" data-lang="ar">العربية</button>';
        header.insertBefore(el,header.querySelector(".nav-cta"));
      }
    }
    if(el){
      const fr=el.querySelector("[data-lang='fr']"),a=el.querySelector("[data-lang='ar']");
      if(fr&&!fr.dataset.bound){fr.onclick=()=>translate("fr");fr.dataset.bound="1";}
      if(a&&!a.dataset.bound){a.onclick=()=>translate("ar");a.dataset.bound="1";}
    }
    const style=document.createElement("style");style.id="mlh-clean-i18n-style";
    style.textContent='body.site-ar{direction:rtl}body.site-ar .hero-copy,body.site-ar .section-heading,body.site-ar .creation-heading,body.site-ar .wizard-card,body.site-ar .price-card,body.site-ar .faq-grid,body.site-ar footer{text-align:right}body.site-ar .site-header nav,body.site-ar .hero-actions,body.site-ar .trust-row,body.site-ar .wizard-actions{direction:rtl}body.site-ar .form-grid input,body.site-ar .form-grid select{direction:rtl}body.site-ar .ar-spaced-heading{font-family:"Noto Kufi Arabic",sans-serif!important;direction:rtl!important;unicode-bidi:plaintext!important;letter-spacing:0!important;word-spacing:normal!important}body.site-ar .hero-copy h1.ar-spaced-heading{font-size:clamp(34px,4.3vw,58px)!important;line-height:1.55!important}body.site-ar #adventures .section-heading h2.ar-spaced-heading,body.site-ar .emotional-card h2.ar-spaced-heading{font-size:clamp(34px,4.5vw,58px)!important;line-height:1.5!important}body.site-ar .creation-heading h2.ar-spaced-heading{font-family:"Noto Kufi Arabic",sans-serif!important;direction:rtl!important;unicode-bidi:plaintext!important;letter-spacing:0!important;word-spacing:.22em!important;line-height:1.55!important}';
    document.head.appendChild(style);
    translate(localStorage.getItem("mlh-site-language")||"fr");
    const order=document.getElementById("orderButton");
    if(order)order.addEventListener("click",e=>{
      if(localStorage.getItem("mlh-site-language")!=="ar")return;
      e.preventDefault();e.stopImmediatePropagation();
      const g=id=>document.getElementById(id)?.textContent?.trim()||"";
      const msg="مرحبًا My Little Hero\nأرغب في طلب مغامرة مخصصة لطفلي.\n\nالبطل: "+(g("summaryName")||"يحدد لاحقًا")+"\nالعمر: "+(g("summaryAge")||"يحدد لاحقًا")+"\nاللغة: العربية\nالباقة: "+g("summaryPack")+"\nالسعر الرقمي: "+g("summaryPrice")+"\n\nأرغب في تأكيد طلبي.";
      window.open("https://wa.me/212603983800?text="+encodeURIComponent(msg),"_blank");
    },true);
  }
  if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",setup);else setup();
})();

(function(){
 const iconMap={"Monde magique":"wand","Fées":"star","Licorne":"unicorn","Royaume":"crown","Dragon":"dragon","Pirates":"ship","Trésor":"treasure","Espace":"rocket","Robots":"robot","Dinosaures":"dino","Sous-marin":"wave","Sirènes":"mermaid","Forêt":"tree","Safari":"lion","Sauvetage":"paw","Football":"ball","Basket":"ball","Course":"car","Détective":"search","Mission secrète":"lock","Chevalier":"shield","Art":"palette","Musique":"music","Danse":"music","Pâtisserie":"cake","Mode":"shirt","Science":"flask","Temps":"clock","Mon propre thème":"spark"};
 const icons={"wand":"<svg viewBox=\"0 0 48 48\" aria-hidden=\"true\"><path d=\"M10 38 35 13\"/><path d=\"m30 8 2 4 4 2-4 2-2 4-2-4-4-2 4-2 2-4Z\"/><path d=\"m11 12 1.5 3 3 1.5-3 1.5-1.5 3-1.5-3-3-1.5 3-1.5 1.5-3Z\"/></svg>","star":"<svg viewBox=\"0 0 48 48\" aria-hidden=\"true\"><path d=\"m24 6 5.2 10.6L41 18.3l-8.5 8.3 2 11.7L24 32.8 13.5 38.3l2-11.7L7 18.3l11.8-1.7L24 6Z\"/></svg>","unicorn":"<svg viewBox=\"0 0 48 48\" aria-hidden=\"true\"><path d=\"M13 34c-2-10 4-18 13-18 6 0 10 4 10 9 0 6-5 10-12 10H13Z\"/><path d=\"m26 16 4-10 3 11\"/><circle cx=\"31\" cy=\"21\" r=\"1.5\"/></svg>","crown":"<svg viewBox=\"0 0 48 48\" aria-hidden=\"true\"><path d=\"m7 14 9 8 8-14 8 14 9-8-4 25H11L7 14Z\"/><path d=\"M11 34h26\"/></svg>","dragon":"<svg viewBox=\"0 0 48 48\" aria-hidden=\"true\"><path d=\"M10 34c5-10 8-16 17-16 6 0 11 4 11 9 0 6-6 10-14 10H10Z\"/><path d=\"m25 18 4-8 3 8M19 19l-6-7 1 10\"/><circle cx=\"31\" cy=\"23\" r=\"1\"/></svg>","ship":"<svg viewBox=\"0 0 48 48\" aria-hidden=\"true\"><path d=\"M9 27h30l-4 10H13L9 27Z\"/><path d=\"M24 27V9M24 10l11 8H24\"/><path d=\"M8 40c4-3 7 3 11 0s7 3 11 0 7 3 11 0\"/></svg>","treasure":"<svg viewBox=\"0 0 48 48\" aria-hidden=\"true\"><path d=\"M8 21h32v18H8z\"/><path d=\"M8 21c1-8 7-12 16-12s15 4 16 12\"/><path d=\"M24 24v9M20 28h8\"/></svg>","rocket":"<svg viewBox=\"0 0 48 48\" aria-hidden=\"true\"><path d=\"M29 8c8 2 11 8 11 14-3 8-10 13-19 15l-6-6c2-9 7-16 14-23Z\"/><circle cx=\"31\" cy=\"17\" r=\"3\"/><path d=\"M17 31 9 39M15 37l-5 1 1-5\"/></svg>","robot":"<svg viewBox=\"0 0 48 48\" aria-hidden=\"true\"><rect x=\"10\" y=\"14\" width=\"28\" height=\"23\" rx=\"5\"/><path d=\"M24 14V8M20 8h8M17 23h.1M31 23h.1M18 30h12\"/></svg>","dino":"<svg viewBox=\"0 0 48 48\" aria-hidden=\"true\"><path d=\"M8 35c5-12 8-20 19-20 7 0 12 4 12 10 0 6-6 9-13 9H8Z\"/><path d=\"m18 17-2-7M25 16l2-8M32 19l6-5\"/><circle cx=\"32\" cy=\"21\" r=\"1\"/></svg>","wave":"<svg viewBox=\"0 0 48 48\" aria-hidden=\"true\"><path d=\"M5 28c5-8 10-8 15 0s10 8 15 0 8-8 8-8\"/><path d=\"M5 36c5-8 10-8 15 0s10 8 15 0 8-8 8-8\"/></svg>","mermaid":"<svg viewBox=\"0 0 48 48\" aria-hidden=\"true\"><path d=\"M25 10c6 0 9 5 8 10-1 4-5 6-9 6l-5 7-7-3 7-8c-4-3-4-9 0-12 2-1 4 0 6 0Z\"/><path d=\"m24 33-8 8 10-4 6 4-2-8\"/></svg>","tree":"<svg viewBox=\"0 0 48 48\" aria-hidden=\"true\"><path d=\"M24 8c-6 0-10 5-8 10-5 1-7 7-4 11 2 3 5 4 8 3v8h8v-8c3 1 6 0 8-3 3-4 1-10-4-11 2-5-2-10-8-10Z\"/><path d=\"M20 40h8\"/></svg>","lion":"<svg viewBox=\"0 0 48 48\" aria-hidden=\"true\"><circle cx=\"24\" cy=\"25\" r=\"11\"/><path d=\"M14 17c-5-4-3-10 2-8M34 17c5-4 3-10-2-8M20 24h.1M28 24h.1M21 29c2 2 4 2 6 0\"/></svg>","paw":"<svg viewBox=\"0 0 48 48\" aria-hidden=\"true\"><path d=\"M24 23c-5-1-10 3-9 8 1 5 7 4 9 1 2 3 8 4 9-1 1-5-4-9-9-8Z\"/><circle cx=\"13\" cy=\"17\" r=\"4\"/><circle cx=\"23\" cy=\"12\" r=\"4\"/><circle cx=\"34\" cy=\"17\" r=\"4\"/></svg>","ball":"<svg viewBox=\"0 0 48 48\" aria-hidden=\"true\"><circle cx=\"24\" cy=\"24\" r=\"15\"/><path d=\"m24 9 5 9-5 6-10-2M29 18l9 4M24 24l1 15M14 22l-5 9M25 39l9-6\"/></svg>","car":"<svg viewBox=\"0 0 48 48\" aria-hidden=\"true\"><path d=\"M9 30 13 19h22l4 11v8H9v-8Z\"/><circle cx=\"16\" cy=\"38\" r=\"3\"/><circle cx=\"33\" cy=\"38\" r=\"3\"/><path d=\"M15 19 18 13h12l3 6\"/></svg>","search":"<svg viewBox=\"0 0 48 48\" aria-hidden=\"true\"><circle cx=\"21\" cy=\"21\" r=\"11\"/><path d=\"m29 29 10 10\"/></svg>","lock":"<svg viewBox=\"0 0 48 48\" aria-hidden=\"true\"><rect x=\"11\" y=\"21\" width=\"26\" height=\"20\" rx=\"3\"/><path d=\"M17 21v-6c0-9 14-9 14 0v6M24 29v5\"/></svg>","shield":"<svg viewBox=\"0 0 48 48\" aria-hidden=\"true\"><path d=\"M24 7 38 13v11c0 9-6 14-14 17-8-3-14-8-14-17V13l14-6Z\"/><path d=\"m17 24 5 5 10-11\"/></svg>","palette":"<svg viewBox=\"0 0 48 48\" aria-hidden=\"true\"><path d=\"M24 9c-10 0-17 7-17 16 0 8 6 14 14 14h4c3 0 4-4 2-6-2-2 0-5 3-5h3c5 0 8-4 8-9 0-6-7-10-17-10Z\"/><circle cx=\"15\" cy=\"23\" r=\"2\"/><circle cx=\"21\" cy=\"17\" r=\"2\"/><circle cx=\"29\" cy=\"17\" r=\"2\"/></svg>","music":"<svg viewBox=\"0 0 48 48\" aria-hidden=\"true\"><path d=\"M31 12v23M31 12l11-3v23M31 35c0 4-4 6-7 4s-1-6 3-7c2-1 4 0 4 3ZM42 32c0 4-4 6-7 4s-1-6 3-7c2-1 4 0 4 3Z\"/></svg>","cake":"<svg viewBox=\"0 0 48 48\" aria-hidden=\"true\"><path d=\"M9 25h30v15H9zM9 25c4 5 8-5 12 0s8-5 12 0 6 0 6 0\"/><path d=\"M16 20v-7M24 20v-9M32 20v-7\"/></svg>","shirt":"<svg viewBox=\"0 0 48 48\" aria-hidden=\"true\"><path d=\"m17 10 7 4 7-4 8 6-5 8-4-3v17H18V21l-4 3-5-8 8-6Z\"/></svg>","flask":"<svg viewBox=\"0 0 48 48\" aria-hidden=\"true\"><path d=\"M19 8h10M22 8v13L12 37c-2 3 1 5 4 5h16c3 0 6-2 4-5L26 21V8\"/><path d=\"M15 32h18\"/></svg>","clock":"<svg viewBox=\"0 0 48 48\" aria-hidden=\"true\"><circle cx=\"24\" cy=\"24\" r=\"16\"/><path d=\"M24 14v11l7 5\"/></svg>","spark":"<svg viewBox=\"0 0 48 48\" aria-hidden=\"true\"><path d=\"M24 6 27 20l15 4-15 4-3 14-3-14-15-4 15-4 3-14Z\"/></svg>"};
 function applyThemeIcons(){
   document.querySelectorAll("[data-theme-label] .theme-icon").forEach(el=>{
     const label=el.parentElement?.dataset.themeLabel;
     const key=iconMap[label]||"spark";
     if(el.dataset.iconKey!==key){el.innerHTML=icons[key];el.dataset.iconKey=key;}
   });
 }
 const style=document.createElement("style");
 style.textContent='
   .theme-choice-grid .theme-icon{display:flex;align-items:center;justify-content:center;color:#5b4bdb}
   .theme-choice-grid .theme-icon svg{width:24px;height:24px;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
   .theme-choice-grid button.selected .theme-icon{color:#5b4bdb}
 ';
 document.head.appendChild(style);
 if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",applyThemeIcons);else applyThemeIcons();
 new MutationObserver(applyThemeIcons).observe(document.body,{childList:true,subtree:true});
})();
(function(){
function bindThemeClicks(){document.querySelectorAll(".theme-choice-grid button").forEach(b=>{b.style.pointerEvents="auto";const i=b.querySelector(".theme-icon");if(i){i.style.pointerEvents="none";i.querySelectorAll("*").forEach(x=>x.style.pointerEvents="none");}})}
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",bindThemeClicks);else bindThemeClicks();
new MutationObserver(bindThemeClicks).observe(document.body,{childList:true,subtree:true});
})();