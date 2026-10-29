"""Generate the two-page proof through the SAME renderer as production, without API calls."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from book_layout import build_book_pdf


def main():
    root = Path(__file__).resolve().parents[1]
    output = root / "output/pdf/itar-maquette-livre-coloriage.pdf"
    page = {"title": "Le panier décisif", "image": root / "examples/itar/story-illustration-v2.png",
        "text": "Itar prend une grande inspiration. Ses amis l’encouragent au bord du terrain. "
            "Il plie les genoux, vise le panier et laisse le ballon s’envoler. "
            "Cette fois, il sait que le plus important est d’oser et de jouer ensemble."}
    build_book_pdf(output, [page], root / "examples/itar/medallion.png", child_name="Itar", gender="boy",
        congratulations="Tu as mené ton équipe jusqu’au panier décisif. Bravo pour ton courage !")
    print(output)


if __name__ == "__main__":
    main()
