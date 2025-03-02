from __future__ import annotations

import requests
from bs4 import BeautifulSoup
import bs4
from dataclasses import dataclass
from pprint import pprint



def get_name_and_gender(idx, children):
    name = children[idx].text
    print(children)
    if isinstance(children[idx], bs4.element.NavigableString):
        # Has a nickname, so `name` is actually the nickname
        name = name.strip("(").strip()
        # Advance by 1 and parse the rest ignoring the nickname
        return_idx, _, species_name, gender = get_name_and_gender(idx + 1, children)
        return (return_idx, name, species_name, gender)
    # If we didn't hit that branch, then there's no nickname and
    # `name` is just the species name
    if name.endswith("("):
        # Gender specified - need to parse it too
        name = name.strip("(").strip()
        new_idx, gender = get_gender(idx + 1, children)
        return (new_idx, name, name, gender)
    return (idx + 1, None, name, None)


def get_gender(idx, children):
    gender = children[idx].text
    return (idx + 1, gender)


def get_item(idx, children):
    maybe_item = children[idx]
    item = maybe_item.split("@")[1].strip() if "@" in maybe_item else None
    return (idx + 1, item)


def get_ability(idx, children):
    if "Ability" not in children[idx].text:
        raise ValueError("u messed up :( (sad)")
    ability = children[idx + 1].strip()
    return (idx + 2, ability)


def get_level(idx, children):
    if "Level" not in children[idx].text:
        raise ValueError("u messed up :( (sad)")
    level = int(children[idx + 1].strip())
    return (idx + 2, level)


def get_tera(idx, children):
    if "Tera Type" not in children[idx].text:
        # Pre-SV mons have no Tera type
        return (idx, None)
    tera_node = children[idx + 1]
    tera_type = tera_node.text.strip()
    if isinstance(tera_node, bs4.element.NavigableString) and "Stellar" in tera_type:
        return idx + 2, "Stellar"
    return idx + 3, tera_type


def get_Vs(idx, children, v_type="EVs"):
    if v_type not in children[idx].text:
        if v_type not in ["EVs", "IVs"]:
            msg = f"{v_type} not one of EVs, IVs (need exact match)"
            raise ValueError(msg)
        return (idx, None)

    V_dct = {}
    n_vs_processed = 0
    possible_keys = ["hp", "atk", "def", "spa", "spd", "spe"]
    while True:
        vs_idx = idx + (n_vs_processed * 2) + 1

        V_stat, V_name = children[vs_idx].text.split()
        if V_name.lower() in possible_keys:
            V_dct[V_name] = int(V_stat)
        else:
            raise UserWarning(f"ummmm are you SuRE? {V_name=}, not in {possible_keys=}")
        n_vs_processed += 1

        if children[vs_idx + 1].strip() != "/":
            break

    return idx + (n_vs_processed * 2), V_dct


def get_nature(idx, children):
    return (idx + 1, children[idx].strip().split()[0])


def get_moves(idx, children):
    should_be_dash = children[idx].text
    num_processed_moves = 0
    moves = []
    while should_be_dash == "-":
        moves.append(children[idx + (num_processed_moves * 2) + 1].strip())
        num_processed_moves += 1
        try:
            should_be_dash = children[idx + (num_processed_moves * 2)].text
        except IndexError:
            # Reached the end of children, no more nodes to process
            break

    return (idx + (num_processed_moves * 2), moves)


def parse_pokemon(pre_block) -> Pokemon:
    children = list(pre_block.children)
    idx = 0
    pk1_dict = {}

    idx, nickname, name, gender = get_name_and_gender(idx, children)
    pk1_dict["nickname"] = nickname
    pk1_dict["name"] = name
    pk1_dict["gender"] = gender

    idx, item = get_item(idx, children)
    pk1_dict["item"] = item

    idx, ability = get_ability(idx, children)
    pk1_dict["ability"] = ability

    idx, level = get_level(idx, children)
    pk1_dict["level"] = level

    idx, tera = get_tera(idx, children)
    pk1_dict["tera"] = tera

    idx, EVs = get_Vs(idx, children, v_type="EVs")
    pk1_dict["EVs"] = EVs

    idx, nature = get_nature(idx, children)
    pk1_dict["nature"] = nature

    idx, IVs = get_Vs(idx, children, v_type="IVs")
    pk1_dict["IVs"] = IVs

    return Pokemon(**pk1_dict)


@dataclass
class Pokemon:
    nickname: str | None
    name: str
    gender: str | None
    item: str | None
    ability: str
    level: int
    tera: str | None
    ability: str
    EVs: dict[str, int]
    nature: str
    IVs: dict[str, int]


@dataclass
class Pokepaste:
    title: str | None
    author: str | None
    notes: str | None
    party: list[Pokemon]


def parse_pokepaste(url: str) -> Pokepaste:
    # Send an HTTP GET request to the URL
    response = requests.get(url)

    # Check if the request was successful (status code 200)
    if response.status_code != 200:
        err_msg = (
            f"Failed to retrieve the webpage {url}. Status code: {response.status_code}"
        )
        raise RuntimeError(err_msg)

    soup = BeautifulSoup(response.text, "html.parser")

    def get_text_in_nested_tag(parent_block, tag_name: str) -> str | None:
        nested_block = parent_block.find(tag_name)
        return nested_block.text if nested_block is not None else None
    
    aside_block = soup.find("aside")
    title = get_text_in_nested_tag(aside_block, "h1")
    author = get_text_in_nested_tag(aside_block, "h2")
    notes = get_text_in_nested_tag(aside_block, "p")
    party = [parse_pokemon(pre_block) for pre_block in soup.find_all("pre")]

    return Pokepaste(title=title, author=author, notes=notes, party=party)

# url = "https://pokepast.es/b6cf9f0fe1fdc4b1"
# # url = "https://pokepast.es/774751c5dc2c4500"
# pprint(parse_pokepaste(url))
# # url = "https://pokepast.es/0124a7741a12bec1i\


# pprint(parse_pokepaste("https://pokepast.es/258e8d89c3a68e97"))

pprint(parse_pokepaste("https://pokepast.es/729d48939b4568fe"))

