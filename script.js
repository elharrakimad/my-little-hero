document.addEventListener("DOMContentLoaded",()=>{const state={pack:1,price:69,name:"",age:"",language:"Français",photo:"",themes:[]};const packNames={1:"Little Hero",2:"Super Hero",3:"Hero Gift"};const prices={1:69,2:119,3:159};const phone="212603983800";const creation=document.getElementById("creation");const cards=[...document.querySelectorAll(".wizard-card")];const labels=[...document.querySelectorAll(".steps-labels span")];const bar=document.getElementById("progressBar");let step=1;const maxThemes=()=>state.pack;function render(){cards.forEach((c,i)=>c.hidden=i+1!==step);bar.style.width=(step*25)+"%";labels.forEach((x,i)=>x.classList.toggle("active",i+1===step))}function openCreation(pack=1){state.pack=Number(pack);state.price=prices[state.pack];state.themes=[];document.querySelectorAll(".choice").forEach(x=>x.classList.toggle("selected",Number(x.dataset.wizardPack)===state.pack));creation.hidden=false;creation.scrollIntoView({behavior:"smooth",block:"start"});step=1;updateAdventureUI();updatePreview();render()}document.querySelectorAll("[data-open-creation]").forEach(b=>b.addEventListener("click",()=>openCreation(state.pack)));document.querySelectorAll("[data-pack]").forEach(b=>b.addEventListener("click",()=>openCreation(b.dataset.pack)));document.querySelectorAll("[data-wizard-pack]").forEach(b=>b.addEventListener("click",()=>{state.pack=Number(b.dataset.wizardPack);state.price=prices[state.pack];state.themes=[];document.querySelectorAll(".choice").forEach(x=>x.classList.toggle("selected",x===b));updateAdventureUI();updatePreview()}));const photoInput=document.getElementById("childPhoto");photoInput.addEventListener("change",e=>{const file=e.target.files[0];if(!file)return;if(file.size>8*1024*1024){alert("La photo doit faire moins de 8 Mo.");photoInput.value="";return}const reader=new FileReader();reader.onload=()=>{state.photo=reader.result;document.getElementById("photoPreviewImg").src=state.photo;document.getElementById("photoPreview").hidden=false};reader.readAsDataURL(file)});document.querySelectorAll(".theme-choice-grid button").forEach(b=>b.addEventListener("click",()=>{const theme=b.dataset.theme;if(state.themes.includes(theme)){state.themes=state.themes.filter(x=>x!==theme)}else{if(state.themes.length>=maxThemes()){alert("Votre pack contient "+maxThemes()+" aventure"+(maxThemes()>1?"s":"")+" .");return}state.themes.push(theme)}document.querySelectorAll(".theme-choice-grid button").forEach(x=>x.classList.toggle("selected",state.themes.includes(x.dataset.theme)));updateAdventureUI();updatePreview()}));function themeLabel(v){return v.replace(/^\s*[\p{Extended_Pictographic}\p{Emoji_Presentation}\uFE0F]+\s*/u,"").trim()}function updateAdventureUI(){const n=maxThemes();document.getElementById("themeInstruction").textContent="Choisissez exactement "+n+" aventure"+(n>1?"s":"")+".";document.getElementById("adventureSlots").innerHTML=Array.from({length:n},(_,i)=>'<span class="adventure-slot '+(state.themes[i]?"done":"")+'">Aventure '+(i+1)+(state.themes[i]?" · "+themeLabel(state.themes[i]):" · à choisir")+"</span>").join("")}document.querySelectorAll(".next").forEach(b=>b.addEventListener("click",async()=>{const currentStep=Number(b.closest(".wizard-card")?.dataset.step||step);if(currentStep===2){state.name=document.getElementById("childName").value.trim();state.age=document.getElementById("childAge").value;state.language=document.getElementById("language").value;const photoFile=photoInput.files?.[0];if(!state.name||!state.age||!photoFile){alert("Veuillez renseigner le prénom, l'âge et la photo de votre enfant.");return}}if(currentStep===3){if(state.themes.length!==maxThemes()){alert("Choisissez exactement "+maxThemes()+" aventure"+(maxThemes()>1?"s":"")+" pour continuer.");return}if(window.generateStoryPreview){b.disabled=true;const ok=await window.generateStoryPreview({name:state.name,age:state.age,language:state.language,themes:state.themes,photoFile:photoInput.files?.[0]});b.disabled=false;if(!ok)return;}}if(step<4)step++;updatePreview();render()}));document.querySelectorAll(".back").forEach(b=>b.addEventListener("click",()=>{if(step>1)step--;render()}));function updatePreview(){document.getElementById("summaryName").textContent=state.name||"Votre enfant";document.getElementById("summaryAge").textContent=state.age||"—";document.getElementById("summaryLang").textContent=state.language;document.getElementById("summaryPack").textContent=packNames[state.pack];document.getElementById("summaryPrice").textContent=state.price+" DH";const previewTitle=document.getElementById("previewTitle");if(previewTitle)previewTitle.textContent=state.name?state.name+" et ses aventures":"Mon aventure";const previewTheme=document.getElementById("previewTheme");if(previewTheme)previewTheme.textContent=state.themes.length?state.themes.map(themeLabel).join(" · "):"Choisissez un univers";document.getElementById("summaryAdventures").innerHTML=state.themes.map((x,i)=>"<div><b>Aventure "+(i+1)+":</b> "+x+"</div>").join("")}document.getElementById("orderButton").addEventListener("click",()=>{const msg="Bonjour My Little Hero\nJe souhaite commander une aventure personnalisée.\n\nHéros : "+(state.name||"À préciser")+"\nÂge : "+(state.age||"À préciser")+"\nLangue : "+state.language+"\nPack : "+packNames[state.pack]+"\nAventures : "+(state.themes.map(themeLabel).join(", ")||"À choisir")+"\nPrix digital : "+state.price+" DH\nPhoto : je l'enverrai dans cette conversation WhatsApp.\n\nJe souhaite valider ma commande.";window.open("https://wa.me/"+phone+"?text="+encodeURIComponent(msg),"_blank")});updateAdventureUI();updatePreview();render()});
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
    "Continuer →":"متابعة →","Retour":"رجوع","Modifier":"تعديل","Voir mon aperçu →":"عرض المعاينة →","Commencer mon histoire →":"ابدأ قصته →",
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
