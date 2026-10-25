from qualite import lire_mesure, valider_code, verdict, analyser_lot, histogramme
from donnees import LOT_A

def test_piece_juste_sous_limite_inferieure():
    mesure = 24.94
    assert verdict(mesure) == "rebut"
def test_code_avec_espaces():
    assert valider_code("  ABC-1234  ") is False

def test_lot_avec_toutes_les_lignes_invalides():
    lot = [
        "ABC-1234;abc",
        "CODE-FAUX;25.01",
    ]

    resultats, erreurs = analyser_lot(lot)

    assert resultats == []
    assert len(erreurs) == 2
def test_histogramme_sans_mesures():
    resultat = histogramme([], debut=25.0, pas=0.1, nb_classes=2)

    assert resultat == (
        "[25.000 ; 25.100[ \n"
        "[25.100 ; 25.200[ "
    )