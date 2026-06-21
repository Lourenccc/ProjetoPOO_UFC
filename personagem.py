"""
RPG Manager — MMA Edition
Módulo: personagem.py
Classes concretas de personagem que herdam de Striker ou Grappler.
Adiciona: HP, vida atual, técnicas por arte, e serialização JSON.
"""

import json
from lutador import (
    Striker, Grappler, Lutador,
    TODAS_AS_ARTES, ARTES_STRIKING, ARTES_GRAPPLING,
    NIVEL_DESBLOQUEIO, CAPS_STRIKER, CAPS_GRAPPLER,
    NivelInsuficienteError, CapAtingidoError, StaminaInsuficienteError
)



# Catálogo de técnicas por arte e nível mínimo
# Estrutura: arte -> lista de (nome_tecnica, nivel_minimo, custo_stamina, multiplicador_dano)

TECNICAS: dict[str, list[tuple]] = {
    "boxe": [
        ("Jab",          1, 8,  1.0),
        ("Direto",       2, 10, 1.2),
        ("Gancho",       3, 13, 1.4),
        ("Uppercut",     5, 15, 1.6),
        ("Combinação",   8, 22, 2.0),
    ],
    "muay_thai": [
        ("Chute Baixo",  1, 10, 1.1),
        ("Chute Médio",  2, 13, 1.3),
        ("Joelhada",     3, 15, 1.5),
        ("Cotovelada",   4, 17, 1.6),
        ("Clinch",       6, 20, 1.8),
        ("Chute Alto",   8, 22, 2.1),
    ],
    "capoeira": [
        ("Ginga",        1,  5, 0.9),
        ("Meia-lua",     2, 12, 1.3),
        ("Armada",       3, 15, 1.5),
        ("Au Batido",    5, 18, 1.7),
        ("Martelo",      7, 21, 2.0),
    ],
    "karate": [
        ("Soco Reto",    1,  8, 1.0),
        ("Chute Frontal",2, 11, 1.2),
        ("Gyaku-zuki",   3, 14, 1.4),
        ("Uraken",       5, 16, 1.6),
        ("Haito",        7, 19, 1.9),
    ],
    "jiu_jitsu": [
        ("Guarda Fechada", 1, 10, 1.0),
        ("Raspagem",       2, 13, 1.2),
        ("Montada",        3, 15, 1.4),
        ("Triângulo",      5, 18, 1.7),
        ("Armlock",        7, 20, 1.9),
        ("Rear Naked Choke",9,23, 2.3),
    ],
    "judo": [
        ("Osoto Gari",   1, 12, 1.1),
        ("Seoi Nage",    2, 15, 1.3),
        ("Harai Goshi",  4, 17, 1.5),
        ("Ippon Seoi",   6, 20, 1.8),
        ("Tomoe Nage",   8, 23, 2.1),
    ],
    "luta_livre": [
        ("Queda Simples",1, 11, 1.0),
        ("Double Leg",   2, 14, 1.3),
        ("Single Leg",   3, 14, 1.3),
        ("Ground & Pound",5,17, 1.6),
        ("Rear Mount",   7, 20, 1.9),
    ],
    "wrestling": [
        ("Clinch",       1, 10, 1.0),
        ("Takedown",     2, 13, 1.2),
        ("Sprawl",       3, 12, 1.1),
        ("Suplex",       5, 18, 1.7),
        ("Slam",         7, 22, 2.0),
    ],
}



# Classe base de Personagem (mixin de HP)

class PersonagemMixin:
    """
    Mixin que adiciona HP ao sistema de Lutador.
    Não herda de Lutador diretamente — é combinado via herança múltipla
    nas classes concretas (ex: Boxeador herda de PersonagemMixin e Striker).
    """

    def _init_hp(self, hp_base: int):
        self._hp_max = hp_base
        self._hp     = hp_base
        self._vivo   = True

    @property
    def hp(self) -> int:
        return self._hp

    @property
    def hp_max(self) -> int:
        return self._hp_max

    @property
    def vivo(self) -> bool:
        return self._vivo

    def receber_dano(self, dano: int) -> int:
        """
        Aplica dano reduzido pela resistência do personagem.
        Retorna o dano efetivo sofrido.
        """
        reducao = self._resistencia // 3   # cada 3 pontos de resistência absorvem 1 de dano
        dano_efetivo = max(1, dano - reducao)
        self._hp -= dano_efetivo
        if self._hp <= 0:
            self._hp   = 0
            self._vivo = False
        return dano_efetivo

    def curar(self, quantidade: int):
        self._hp = min(self._hp + quantidade, self._hp_max)

    def esta_ko(self) -> bool:
        return not self._vivo

    def barra_hp(self) -> str:
        """Retorna uma barra visual de HP."""
        proporcao  = self._hp / self._hp_max
        blocos     = int(proporcao * 20)
        cor        = "🟩" if proporcao > 0.5 else ("🟨" if proporcao > 0.25 else "🟥")
        return f"HP [{cor * blocos}{'⬛' * (20 - blocos)}] {self._hp}/{self._hp_max}"

    def barra_stamina(self) -> str:
        """Retorna uma barra visual de stamina."""
        proporcao = self._stamina / self._stamina_max
        blocos    = int(proporcao * 20)
        return f"ST [{'🟦' * blocos}{'⬛' * (20 - blocos)}] {self._stamina}/{self._stamina_max}"

    #Técnicas disponíveis

    def tecnicas_disponiveis(self) -> dict[str, list[dict]]:
        """
        Retorna todas as técnicas que o personagem pode usar agora,
        agrupadas por arte marcial.
        """
        disponiveis = {}
        for arte, lista in TECNICAS.items():
            if not self.arte_desbloqueada(arte):
                continue
            nivel = self.nivel_arte(arte)
            tecnicas_arte = [
                {"nome": nome, "nivel_min": nmin, "custo": custo, "mult": mult}
                for nome, nmin, custo, mult in lista
                if nivel >= nmin
            ]
            if tecnicas_arte:
                disponiveis[arte] = tecnicas_arte
        return disponiveis

    def usar_tecnica(self, alvo: "Lutador", arte: str, indice_tecnica: int) -> tuple[int, str]:
        """
        Executa uma técnica específica contra um alvo.
        Usa o método atacar() da classe pai (Striker ou Grappler) mas
        com o multiplicador e custo de stamina da técnica escolhida.
        """
        if not self.arte_desbloqueada(arte):
            raise NivelInsuficienteError(f"{arte} não está desbloqueada.")

        tecnicas_arte = [
            (nome, nmin, custo, mult)
            for nome, nmin, custo, mult in TECNICAS[arte]
            if self.nivel_arte(arte) >= nmin
        ]

        if not tecnicas_arte:
            raise NivelInsuficienteError(f"Nenhuma técnica disponível em {arte}.")

        if indice_tecnica < 0 or indice_tecnica >= len(tecnicas_arte):
            raise IndexError("Técnica inválida.")

        nome, _, custo, mult = tecnicas_arte[indice_tecnica]

        # Verifica e consome stamina
        self.consumir_stamina(custo)

        # Calcula dano base conforme a classe (Striker usa força, Grappler usa resistência)
        nivel_arte = self.nivel_arte(arte)
        if isinstance(self, Striker):
            bonus_classe = 1.2 if arte in ARTES_STRIKING else 0.8
            base = self._forca
        else:
            bonus_classe = 1.2 if arte in ARTES_GRAPPLING else 0.8
            base = self._resistencia

        dano_bruto = int((base + nivel_arte * 2) * mult * bonus_classe)

        # Aplica dano no alvo (se tiver mixin de HP)
        if isinstance(alvo, PersonagemMixin):
            dano_efetivo = alvo.receber_dano(dano_bruto)
            log = (
                f"{self._nome} usou [{nome}] ({arte.replace('_',' ').title()}) "
                f"→ {dano_efetivo} de dano em {alvo.nome}! "
                f"(HP: {alvo.hp}/{alvo.hp_max})"
            )
            if alvo.esta_ko():
                log += f"\n💀 {alvo.nome} foi nocauteado!"
        else:
            dano_efetivo = dano_bruto
            log = f"⚔️  {self._nome} usou [{nome}] causando {dano_efetivo} de dano!"

        return dano_efetivo, log

    # Serialização (salvar no json)
    def para_dict(self) -> dict:
        """Serializa o personagem para um dicionário (para salvar em JSON)."""
        return {
            "classe":      self.__class__.__name__,
            "tipo":        "Striker" if isinstance(self, Striker) else "Grappler",
            "nome":        self._nome,
            "nivel":       self._nivel,
            "xp":          self._xp,
            "forca":       self._forca,
            "resistencia": self._resistencia,
            "agilidade":   self._agilidade,
            "stamina_max": self._stamina_max,
            "stamina":     self._stamina,
            "hp_max":      self._hp_max,
            "hp":          self._hp,
            "artes":       self._artes,
        }

    def status_completo(self) -> str:
        nome_tipo = "Striker" if isinstance(self, Striker) else "Grappler"
        artes_ativas = {k: v for k, v in self._artes.items() if v > 0}
        caps = self._caps()
        artes_str = "\n".join(
            f"   {'🔵' if k in ARTES_STRIKING else '🟤'} "
            f"{k.replace('_',' ').title():15} lv.{v}/{caps[k]}"
            for k, v in artes_ativas.items()
        )
        return (
            f"╔══ {self._nome} ══ {self.__class__.__name__} ({nome_tipo}) ══ Nível {self._nivel} ╗\n"
            f"  {self.barra_hp()}\n"
            f"  {self.barra_stamina()}\n"
            f"  Força: {self._forca}  Resistência: {self._resistencia}  Agilidade: {self._agilidade}\n"
            f"  XP: {self._xp} (faltam {self.xp_para_proximo_nivel()} para lv.{self._nivel+1})\n"
            f"  Artes Marciais:\n{artes_str}\n"
            f"╚{'═' * 50}╝"
        )

# Classes concretas — Strikers
class Boxeador(PersonagemMixin, Striker): #heranca multipla
    """Especialista em boxe. Maior força de soco, rápido e preciso."""

    def __init__(self, nome: str, forca: int = 8, resistencia: int = 6,
                 agilidade: int = 8, stamina_max: int = 100, hp_base: int = 90):
        Striker.__init__(self, nome, forca, resistencia, agilidade, stamina_max)
        self._init_hp(hp_base)
        # Boxeador começa com boxe já no nível 2
        self._artes["boxe"] = 2

    def atacar(self, alvo, arte="boxe"):
        return self.usar_tecnica(alvo, arte, 0)


class MuayThaiLutador(PersonagemMixin, Striker): #heranca multipla
    """Especialista em Muay Thai. Forte, resistente e brutal no clinch."""

    def __init__(self, nome: str, forca: int = 7, resistencia: int = 8,
                 agilidade: int = 6, stamina_max: int = 110, hp_base: int = 100):
        Striker.__init__(self, nome, forca, resistencia, agilidade, stamina_max)
        self._init_hp(hp_base)

    def atacar(self, alvo, arte="muay_thai"):
        return self.usar_tecnica(alvo, arte, 0)


class Capoeirista(PersonagemMixin, Striker): #heranca multipla
    #Especialista em Capoeira.

    def __init__(self, nome: str, forca: int = 6, resistencia: int = 6,
                 agilidade: int = 10, stamina_max: int = 105, hp_base: int = 85):
        Striker.__init__(self, nome, forca, resistencia, agilidade, stamina_max)
        self._init_hp(hp_base)

    def atacar(self, alvo, arte="capoeira"):
        return self.usar_tecnica(alvo, arte, 0)

# Classes concretas — Grapplers
class AtletaJJ(PersonagemMixin, Grappler): #heranca multipla
    #Especialista em Jiu-Jitsu.

    def __init__(self, nome: str, forca: int = 6, resistencia: int = 9,
                 agilidade: int = 6, stamina_max: int = 105, hp_base: int = 100):
        Grappler.__init__(self, nome, forca, resistencia, agilidade, stamina_max)
        self._init_hp(hp_base)
        self._artes["jiu_jitsu"] = 2

    def atacar(self, alvo, arte="jiu_jitsu"):
        return self.usar_tecnica(alvo, arte, 0)


class Judoca(PersonagemMixin, Grappler): #heranca multipla
    #Especialista em Judô.  

    def __init__(self, nome: str, forca: int = 8, resistencia: int = 8,
                 agilidade: int = 6, stamina_max: int = 100, hp_base: int = 105):
        Grappler.__init__(self, nome, forca, resistencia, agilidade, stamina_max)
        self._init_hp(hp_base)

    def atacar(self, alvo, arte="judo"):
        return self.usar_tecnica(alvo, arte, 0)


class LutadorLivre(PersonagemMixin, Grappler): #heranca multipla
    #Especialista em Luta Livre.

    def __init__(self, nome: str, forca: int = 7, resistencia: int = 8,
                 agilidade: int = 7, stamina_max: int = 100, hp_base: int = 95):
        Grappler.__init__(self, nome, forca, resistencia, agilidade, stamina_max)
        self._init_hp(hp_base)

    def atacar(self, alvo, arte="luta_livre"):
        return self.usar_tecnica(alvo, arte, 0)



# Fábrica de personagens (Factory)
CLASSES_DISPONIVEIS = {
    "Boxeador":        Boxeador,
    "MuayThaiLutador": MuayThaiLutador,
    "Capoeirista":     Capoeirista,
    "AtletaJJ":        AtletaJJ,
    "Judoca":          Judoca,
    "LutadorLivre":    LutadorLivre,
}

def criar_personagem(classe: str, nome: str, **kwargs): #Factory cria um personagem pelo nome da classe.
    if classe not in CLASSES_DISPONIVEIS:
        raise ValueError(f"Classe '{classe}' não existe. Opções: {list(CLASSES_DISPONIVEIS)}")
    return CLASSES_DISPONIVEIS[classe](nome, **kwargs)


def carregar_personagem(dados: dict):
    """Reconstrói um personagem a partir de um dicionário (carregado do JSON)."""
    classe_nome = dados["classe"]
    p = criar_personagem(classe_nome, dados["nome"])
    p._nivel       = dados["nivel"]
    p._xp          = dados["xp"]
    p._forca       = dados["forca"]
    p._resistencia = dados["resistencia"]
    p._agilidade   = dados["agilidade"]
    p._stamina_max = dados["stamina_max"]
    p._stamina     = dados["stamina"]
    p._hp_max      = dados["hp_max"]
    p._hp          = dados["hp"]
    p._artes       = dados["artes"]
    p._vivo        = dados["hp"] > 0
    return p
