"""Catalogue commercial : prix hors livraison, calculés côté serveur."""
import json
from pathlib import Path
PACKS = {p["id"]: p for p in json.loads(Path(__file__).with_name("packs.json").read_text(encoding="utf-8"))}
def get_pack(pack_id):
    if type(pack_id) is not int or pack_id not in PACKS:
        raise ValueError("Veuillez choisir un pack valide.")
    return PACKS[pack_id]
