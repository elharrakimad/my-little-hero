document.addEventListener("DOMContentLoaded",()=>{
  const API_BASE="https://my-little-hero.onrender.com";
  const orderButton=document.getElementById("orderButton");
  const coverBox=document.getElementById("generatedCoverBox");
  const booksBox=document.getElementById("generatedBooks");
  const titleList=document.getElementById("generatedCoverTitleList");
  const coverStatus=document.getElementById("coverStatus");

  if(!orderButton||!coverBox||!booksBox||!coverStatus)return;

  orderButton.disabled=true;
  orderButton.setAttribute("aria-disabled","true");

  window.generateStoryPreview=async({name,age,language,themes,photoFile})=>{
    if(!name||!age||!photoFile||!themes?.length)return false;

    const form=new FormData();
    form.append("child_name",name);
    form.append("child_age",age);
    form.append("language",language||"Français");
    form.append("themes",JSON.stringify(themes));
    form.append("theme",themes[0]||"");
    form.append("photo",photoFile);

    const button=document.querySelector('[data-step="3"] .next');
    const originalLabel=button?.textContent||"Commencer mon histoire →";
    if(button){button.disabled=true;button.textContent=document.documentElement.lang==="ar"?"جارٍ إنشاء قصته…":"Création de son histoire…";}

    coverStatus.textContent=document.documentElement.lang==="ar"?"نحن ننشئ كتبه…":"Nous créons ses livres…";
    orderButton.disabled=true;
    orderButton.setAttribute("aria-disabled","true");
    coverBox.hidden=true;
    booksBox.innerHTML="";
    titleList.innerHTML="";

    try{
      const response=await fetch(API_BASE+"/api/preview-cover",{method:"POST",body:form});
      let data={};
      try{data=await response.json();}catch(_){data={};}
      if(!response.ok)throw new Error(data.detail||"Erreur de génération.");
      if(!Array.isArray(data.covers)||!data.covers.length)throw new Error("Aucune couverture générée.");

      data.covers.forEach((cover,index)=>{
        const book=document.createElement("div");
        book.className="generated-book generated-book-"+data.covers.length+" book-index-"+index;
        const img=document.createElement("img");
        img.src=cover.cover_data_url;
        img.alt=cover.title||"Livre personnalisé";
        book.appendChild(img);
        booksBox.appendChild(book);

        const title=document.createElement("div");
        title.className="generated-cover-title-item";
        title.innerHTML="<b>"+(index+1)+"</b><span>"+escapeHtml(cover.title||"")+"</span>";
        titleList.appendChild(title);
      });

      coverBox.hidden=false;
      coverStatus.textContent=document.documentElement.lang==="ar"?"كتبك جاهزة للمعاينة.":"Vos livres sont prêts à être découverts.";
      orderButton.disabled=false;
      orderButton.removeAttribute("aria-disabled");
      return true;
    }catch(error){
      console.error(error);
      coverStatus.textContent=document.documentElement.lang==="ar"?"تعذر إنشاء المعاينة.":"Impossible de créer l’aperçu."; 
      alert(document.documentElement.lang==="ar"?"تعذر إنشاء الكتب الآن. يرجى المحاولة مرة أخرى.":"La création des livres a échoué. Veuillez réessayer.");
      return false;
    }finally{
      if(button){button.disabled=false;button.textContent=originalLabel;}
    }
  };

  function escapeHtml(value){
    return String(value).replace(/[&<>'"]/g,char=>({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;","\"":"&quot;"}[char]));
  }
});
