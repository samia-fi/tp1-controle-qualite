"""Contrôle qualité d'une ligne d'usinage : lecture des mesures, verdicts, statistiques, rapport."""
import math

NOMINAL = 25.0     # diamètre nominal des axes, en mm
TOLERANCE = 0.05   # tolérance admise : 25,00 ± 0,05 mm


# --- Étape 1 : lire les données -----------------------------------------------------------------
def lire_mesure(texte: str) -> float:
    """Convertit une mesure saisie par le palpeur en nombre : " 25,03 mm" -> 25.03.

    Accepte la virgule ou le point, l'unité "mm" (collée ou non) et les espaces autour.
    Lève ValueError si le texte n'est pas une mesure strictement positive et finie.
    """
    
    texte = texte.strip().lower()
    texte = texte.removesuffix("mm").strip()
    texte = texte.replace(",", ".")

    try:
        x = float(texte)
    except ValueError:
        raise ValueError(f"mesure invalide : {texte.strip()!r}")

    import math
    if not math.isfinite(x) or x <= 0:
        raise ValueError(f"mesure invalide : {texte.strip()!r}")

    return x



def valider_code(code: str) -> bool:
    """Vrai si le code pièce respecte le format AAA-9999 : trois majuscules, un tiret, quatre chiffres."""
    
    return (
        len(code) == 8
        and code[:3].isalpha()
        and code[:3].isascii()
        and code[:3].isupper()
        and code[3] == "-"
        and code[4:].isdigit()
        and code[4:].isascii()
    )



# --- Étape 2 : décider ----------------------------------------------------------------------------
def ecart(mesure: float, nominal: float = NOMINAL) -> float:
    """Écart à la cote nominale, arrondi au micromètre (3 décimales) pour éliminer le bruit des flottants."""
    return round(mesure - nominal, 3)


def verdict(mesure: float, nominal: float = NOMINAL, tolerance: float = TOLERANCE) -> str:
    """Renvoie "conforme", "à reprendre" (trop gros : on peut réusiner) ou "rebut" (trop petit)."""
    if tolerance <= 0:
        raise ValueError("La tolérance doit être positive")

    e = ecart(mesure, nominal)

    if abs(e) <= tolerance:
        return "conforme"
    elif e > 0:
        return "à reprendre"
    else:
        return "rebut" 


# --- Étape 3 : analyser une ligne -----------------------------------------------------------------
def analyser_ligne(ligne: str, *, nominal: float = NOMINAL, tolerance: float = TOLERANCE) -> tuple[str, float, str]:
    """Analyse une ligne "AXE-0042 ; 25,03 mm" et renvoie (code, mesure, verdict).

    Lève ValueError si la ligne n'a pas deux champs, si le code ou la mesure est invalide.
    """
    champs = ligne.split(";")

    if len(champs) != 2:
        raise ValueError(f"2 champs attendus, {len(champs)} trouvé(s)")

    code = champs[0].strip().upper()
    mesure_txt = champs[1].strip()

    if not valider_code(code):
        raise ValueError(f"code invalide : {code!r}")

    mesure = lire_mesure(mesure_txt)
    v = verdict(mesure, nominal=nominal, tolerance=tolerance)

    return code, mesure, v


# --- Étape 4 : analyser un lot --------------------------------------------------------------------
def analyser_lot(lignes: list[str], **reglages) -> tuple[list[tuple[str, float, str]], list[str]]:
    """Analyse toutes les lignes d'un lot et renvoie (resultats, erreurs).

    Les lignes vides et les commentaires (#) sont ignorés. Une ligne invalide n'arrête pas l'analyse :
    son message est ajouté à erreurs, sous la forme "ligne 4 : mesure invalide : 'abc'".
    Les réglages (nominal, tolerance) sont transmis tels quels à analyser_ligne.
    """
    resultats = []
    erreurs = []

    for numero, ligne in enumerate(lignes, start=1):
        ligne = ligne.strip()

        if not ligne or ligne.startswith("#"):
            continue

        try:
            resultat = analyser_ligne(ligne, **reglages)
            resultats.append(resultat)
        except ValueError as e:
            erreurs.append(f"ligne {numero} : {e}")

    return resultats, erreurs


def compter_verdicts(resultats: list[tuple[str, float, str]]) -> tuple[int, int, int]:
    """Renvoie le nombre de pièces (conformes, à reprendre, rebuts)."""
    conformes = 0
    a_reprendre = 0
    rebuts = 0

    for code, mesure, v in resultats:
     if v == "conforme":
        conformes += 1
     elif v == "à reprendre":
        a_reprendre += 1
     elif v == "rebut":
        rebuts += 1
    return conformes, a_reprendre, rebuts


# --- Étape 5 : statistiques et capabilité ---------------------------------------------------------
def moyenne(*valeurs: float) -> float:
    """Moyenne d'un nombre quelconque de valeurs. Lève ValueError s'il n'y en a aucune."""
    if not valeurs:
     raise ValueError("au moins une valeur est nécessaire")

    return sum(valeurs) / len(valeurs)


def ecart_type(*valeurs: float) -> float:
    """Écart type d'échantillon (division par n - 1). Lève ValueError avec moins de deux valeurs."""
    if len(valeurs) < 2:
     raise ValueError("au moins deux valeurs sont nécessaires")

    m = moyenne(*valeurs)
    somme_carres = sum((x - m) ** 2 for x in valeurs)

    return (somme_carres / (len(valeurs) - 1)) ** 0.5


def capabilite(mesures: list[float], *, nominal: float = NOMINAL, tolerance: float = TOLERANCE) -> tuple[float, float]:
    """Indices de capabilité (Cp, Cpk), arrondis à 2 décimales.

    Cp  = largeur de la tolérance / (6 sigma)                  : le procédé est-il assez précis ?
    Cpk = distance de la moyenne à la limite la plus proche / (3 sigma) : est-il bien centré ?
    """
    if tolerance <= 0:
        raise ValueError("la tolérance doit être strictement positive")

    if len(mesures) < 2:
        raise ValueError("au moins deux mesures sont nécessaires")

    sigma = ecart_type(*mesures)

    if sigma == 0:
        raise ValueError("écart-type nul : capabilité impossible")

    m = moyenne(*mesures)
    limite_basse = nominal - tolerance
    limite_haute = nominal + tolerance

    cp = (limite_haute - limite_basse) / (6 * sigma)
    cpk = min(limite_haute - m, m - limite_basse) / (3 * sigma)

    return round(cp, 2), round(cpk, 2)



# --- Étape 6 : le rapport -------------------------------------------------------------------------
def rapport(lignes: list[str], *, nominal: float = NOMINAL, tolerance: float = TOLERANCE) -> str:
    """Construit le rapport de contrôle d'un lot, sous forme d'une seule chaîne (une ligne par pièce)."""
    raise NotImplementedError("à compléter")


# --- Étape 8 (à la maison) : histogramme ----------------------------------------------------------
def histogramme(mesures: list[float], *, debut: float, pas: float, nb_classes: int) -> str:
    """Histogramme texte : une ligne par classe [borne, borne + pas[, une étoile par mesure.

    Les mesures hors de [debut, debut + nb_classes * pas[ sont ignorées.
    """
    raise NotImplementedError("à compléter")
