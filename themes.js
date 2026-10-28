document.addEventListener("DOMContentLoaded", () => {
  const gender = document.getElementById("childGender");
  const grid = document.querySelector(".theme-choice-grid");
  if (!gender || !grid) return;
  const suggestions = {
    girl: new Set(["Fées", "Licorne", "Royaume", "Sirènes", "Art", "Musique", "Danse", "Pâtisserie", "Mode"]),
    boy: new Set(["Dragon", "Pirates", "Espace", "Robots", "Dinosaures", "Football", "Basket", "Course", "Mission secrète", "Chevalier"]),
  };
  const common = new Set(["Monde magique", "Trésor", "Sous-marin", "Forêt", "Safari", "Sauvetage", "Détective", "Science", "Temps", "Mon propre thème"]);
  const toggle = document.createElement("button");
  toggle.type = "button";
  toggle.className = "btn btn-ghost";
  grid.before(toggle);
  let showAll = false;
  function render() {
    const ar = document.documentElement.lang === "ar";
    toggle.textContent = showAll
      ? (ar ? "عرض الاقتراحات" : "Voir les suggestions")
      : (ar ? "عرض جميع المواضيع" : "Voir tous les thèmes");
    toggle.setAttribute("aria-expanded", String(showAll));
    grid.querySelectorAll("button").forEach(button => {
      const label = button.dataset.themeLabel;
      button.hidden = !showAll && !!suggestions[gender.value]
        && !suggestions[gender.value].has(label) && !common.has(label);
    });
  }
  toggle.addEventListener("click", () => { showAll = !showAll; render(); });
  gender.addEventListener("change", () => { showAll = false; render(); });
  new MutationObserver(render).observe(document.documentElement, {attributes: true, attributeFilter: ["lang"]});
  render();
});
