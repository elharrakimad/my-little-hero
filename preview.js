document.addEventListener("DOMContentLoaded",()=>{
  const API_BASE="https://my-little-hero-api.onrender.com";
  const generateButton=document.getElementById("generateCoverButton");
  const orderButton=document.getElementById("orderButton");
  const coverBox=document.getElementById("generatedCoverBox");
  const coverImage=document.getElementById("generatedCoverImage");
  const coverTitle=document.getElementById("generatedCoverTitle");
  const coverStatus=document.getElementById("coverStatus");
  const photoInput=document.getElementById("childPhoto");

  if(!generateButton||!orderButton||!photoInput)return;

  orderButton.disabled=true;
  orderButton.setAttribute("aria-disabled","true");

  generateButton.addEventListener("click",async()=>{
    const name=document.getElementById("childName")?.value.trim();
    const age=document.getElementById("childAge")?.value;
    const language=document.getElementById("language")?.value||"Français";
    const themeButtons=[...document.querySelectorAll(".theme-choice-grid button.selected")];
    const theme=themeButtons[0]?.dataset.theme||"";
    const photo=photoInput.files?.[0];

    if(!name||!age||!photo||!theme){
      alert("Veuillez renseigner le prénom, l'âge, la photo et choisir une aventure.");
      return;
    }

    const form=new FormData();
    form.append("child_name",name);
    form.append("child_age",age);
    form.append("language",language);
    form.append("theme",theme);
    form.append("photo",photo);

    generateButton.disabled=true;
    orderButton.disabled=true;
    coverBox.hidden=false;
    coverStatus.textContent="Création de la couverture...";
    coverImage.hidden=true;
    coverTitle.textContent="";

    try{
      const response=await fetch(API_BASE+"/api/preview-cover",{method:"POST",body:form});
      const data=await response.json();
      if(!response.ok)throw new Error(data.detail||"Erreur de génération.");

      coverImage.src=data.cover_data_url;
      coverImage.hidden=false;
      coverTitle.textContent=data.title||"";
      coverStatus.textContent="Votre couverture est prête.";
      orderButton.disabled=false;
      orderButton.removeAttribute("aria-disabled");
      coverBox.scrollIntoView({behavior:"smooth",block:"center"});
    }catch(error){
      console.error(error);
      coverStatus.textContent="Impossible de générer l'aperçu. Veuillez réessayer.";
      alert("La génération de la couverture a échoué. Vérifiez que le backend est en ligne puis réessayez.");
    }finally{
      generateButton.disabled=false;
    }
  });
});
