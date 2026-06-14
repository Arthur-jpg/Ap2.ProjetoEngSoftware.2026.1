"""Lógica pura de parsing do XML do SpotBugs (Fase 4).

Separada do orquestrador (`run_spotbugs.py`) para ser testável sem precisar
rodar o SpotBugs nem depender do pandas. Conta <BugInstance> por classe,
colapsando classes internas/anônimas (Foo$Bar → Foo) para casar com a saída
do CK na Fase 5.
"""
import xml.etree.ElementTree as ET

from utils import normalize_class_name


def count_bugs_by_class(xml_text: str) -> dict[str, int]:
    """Conta bugs por classe a partir do texto XML do SpotBugs.

    Garante o critério de aceite da Fase 4: a soma das contagens é igual ao
    número total de <BugInstance> que possuem uma classe associada.

    Retorna {nome_classe_normalizado: contagem}.
    """
    root = ET.fromstring(xml_text)
    counts: dict[str, int] = {}

    for bug in root.iter("BugInstance"):
        cls_el = bug.find("Class")
        if cls_el is None:
            cls_el = bug.find("SourceLine")
        if cls_el is None:
            continue
        classname = cls_el.get("classname", "")
        if not classname:
            continue
        key = normalize_class_name(classname)
        counts[key] = counts.get(key, 0) + 1

    return counts
