"""
Módulo: lutador.py
Lutador → Striker / Grappler
"""

from abc import ABC, abstractmethod

# Exceções customizadas
class NivelInsuficienteError(Exception):
    #quando o lutador tenta usar uma arte ainda não desbloqueada
    pass

class CapAtingidoError(Exception):
   #quando o nível de uma arte atinge o limite da classe
    pass

class StaminaInsuficienteError(Exception):
    #Lançada quando não há stamina suficiente para executar uma ação
    pass

class AtributoInvalidoError(Exception):
    #Lançada ao tentar definir um atributo com valor inválido
    pass



# Constantes globais

# Artes marciais disponíveis no jogo - lista de artes marciais
ARTES_STRIKING  = ["boxe", "muay_thai", "capoeira", "karate"]
ARTES_GRAPPLING = ["jiu_jitsu", "judo", "luta_livre", "wrestling"]
TODAS_AS_ARTES  = ARTES_STRIKING + ARTES_GRAPPLING

# Nível geral necessário para desbloquear cada arte
NIVEL_DESBLOQUEIO = {
    "boxe":       1,   # disponível desde o início
    "muay_thai":  3,
    "capoeira":   5,
    "karate":     4,
    "jiu_jitsu":  1,   # disponível desde o início
    "judo":       3,
    "luta_livre": 4,
    "wrestling":  5,
}

# Caps por classe (nível máximo que cada classe pode atingir em cada arte)
CAPS_STRIKER = {
    "boxe":       10,
    "muay_thai":  10,
    "capoeira":   8,
    "karate":     8,
    "jiu_jitsu":  4,   
    "judo":       3,
    "luta_livre": 4,
    "wrestling":  3,
}

CAPS_GRAPPLER = {
    "boxe":       4,  
    "muay_thai":  3,
    "capoeira":   2,
    "karate":     3,
    "jiu_jitsu":  10,
    "judo":       10,
    "luta_livre": 8,
    "wrestling":  8,
}



# Classe abstrata base
class Lutador(ABC):
    
    #Classe abstrata para qualquer lutador
    #Define atributos físicos, nível geral e as artes marciais.
    

    def __init__(self, nome: str, forca: int = 5, resistencia: int = 5, agilidade: int = 5, stamina_max: int = 100):

        # Atributos físicos
        self._nome       = nome
        self._forca      = forca
        self._resistencia = resistencia
        self._agilidade  = agilidade
        self._stamina_max = stamina_max
        self._stamina    = stamina_max   # stamina atual começa cheia
        self._nivel      = 1
        self._xp         = 0

        # Dicionário de níveis em cada arte marcial
        self._artes: dict[str, int] = {arte: 0 for arte in TODAS_AS_ARTES}

        # Artes desbloqueadas no nível 1 são abertas automaticamente
        for arte, nivel_req in NIVEL_DESBLOQUEIO.items():
            if nivel_req <= self._nivel:
                self._artes[arte] = 1   # nível 1 = desbloqueado mas iniciante

    # ── Properties de atributos físicos ──────────────────────────────

    @property
    def nome(self) -> str:
        return self._nome

    @property
    def nivel(self) -> int:
        return self._nivel

    @property
    def xp(self) -> int:
        return self._xp

    @property
    def forca(self) -> int:
        return self._forca

    @forca.setter
    def forca(self, valor: int):
        if valor < 1 or valor > 20:
            raise AtributoInvalidoError("Força deve estar entre 1 e 20.")
        self._forca = valor

    @property
    def resistencia(self) -> int:
        return self._resistencia

    @resistencia.setter
    def resistencia(self, valor: int):
        if valor < 1 or valor > 20:
            raise AtributoInvalidoError("Resistência deve estar entre 1 e 20.")
        self._resistencia = valor

    @property
    def agilidade(self) -> int:
        return self._agilidade

    @agilidade.setter
    def agilidade(self, valor: int):
        if valor < 1 or valor > 20:
            raise AtributoInvalidoError("Agilidade deve estar entre 1 e 20.")
        self._agilidade = valor

    @property
    def stamina(self) -> int:
        return self._stamina

    @property
    def stamina_max(self) -> int:
        return self._stamina_max

    # Métodos de nível geral

    def ganhar_xp(self, quantidade: int):
        #Adiciona XP e verifica se deve subir de nível.
        
        self._xp += quantidade
        xp_necessario = self._nivel * 100   # cada nível exige 100*nível XP
        while self._xp >= xp_necessario:
            self._xp -= xp_necessario
            self._subir_nivel()
            xp_necessario = self._nivel * 100

    def _subir_nivel(self):
        #Sobe o nível geral e desbloqueia novas artes se aplicável.
        self._nivel += 1
        print(f"\n{self._nome} subiu para o nível {self._nivel}!")

        # Verifica se alguma arte foi desbloqueada
        for arte, nivel_req in NIVEL_DESBLOQUEIO.items():
            if nivel_req == self._nivel and self._artes[arte] == 0:
                self._artes[arte] = 1
                print(f"Arte desbloqueada: {arte.replace('_', ' ').title()}!")

    def xp_para_proximo_nivel(self) -> int:
        return self._nivel * 100 - self._xp

    # ── Métodos de artes marciais ─────────────────────────────────────

    def nivel_arte(self, arte: str) -> int:
        """Retorna o nível atual em uma arte marcial (0 = bloqueada)."""
        if arte not in TODAS_AS_ARTES:
            raise ValueError(f"Arte '{arte}' não existe no sistema.")
        return self._artes[arte]

    def arte_desbloqueada(self, arte: str) -> bool:
        return self._artes.get(arte, 0) > 0

    @abstractmethod
    def _caps(self) -> dict[str, int]:
        """Retorna o dicionário de caps desta classe. Implementado nas subclasses."""
        pass

    def treinar_arte(self, arte: str):
        """
        Sobe o nível em uma arte marcial em +1.
        Lança exceções se a arte estiver bloqueada ou no cap da classe.
        """
        if arte not in TODAS_AS_ARTES:
            raise ValueError(f"Arte '{arte}' não existe.")

        if not self.arte_desbloqueada(arte):
            nivel_req = NIVEL_DESBLOQUEIO[arte]
            raise NivelInsuficienteError(
                f"{arte.replace('_',' ').title()} requer nível geral {nivel_req}. "
                f"Você está no nível {self._nivel}."
            )

        cap = self._caps()[arte]
        if self._artes[arte] >= cap:
            raise CapAtingidoError(
                f"Você atingiu o limite de {cap} em "
                f"{arte.replace('_',' ').title()} para sua classe."
            )

        self._artes[arte] += 1
        print(f"{arte.replace('_',' ').title()} agora está no nível {self._artes[arte]}/{cap}.")

    # Stamina
    def consumir_stamina(self, quantidade: int):
        if self._stamina < quantidade:
            raise StaminaInsuficienteError(
                f"Stamina insuficiente! Tem {self._stamina}, precisa de {quantidade}."
            )
        self._stamina -= quantidade

    def recuperar_stamina(self, quantidade: int):
        self._stamina = min(self._stamina + quantidade, self._stamina_max)

    def recuperar_stamina_total(self):
        self._stamina = self._stamina_max

    #Método abstrato de combate
    @abstractmethod
    def atacar(self, alvo: "Lutador", arte: str) -> str:
        """
        implementado em cada subclasse concreta.
        Retorna uma string descrevendo a ação (log de combate).
        """
        pass

    #Representação
    def status(self) -> str:
        artes_ativas = {
            k: v for k, v in self._artes.items() if v > 0
        }
        artes_str = ", ".join(
            f"{k.replace('_',' ').title()} lv.{v}" for k, v in artes_ativas.items()
        )
        return (
            f"┌─ {self._nome} ({'Striker' if isinstance(self, Striker) else 'Grappler'}) "
            f"── Nível {self._nivel}\n"
            f"│  Força: {self._forca}  Resistência: {self._resistencia}  "
            f"Agilidade: {self._agilidade}\n"
            f"│  Stamina: {self._stamina}/{self._stamina_max}\n"
            f"│  XP: {self._xp} (faltam {self.xp_para_proximo_nivel()} para o próximo nível)\n"
            f"│  Artes: {artes_str or 'nenhuma'}\n"
            f"└{'─' * 50}"
        )

    def __str__(self) -> str:
        return f"{self._nome} (Nível {self._nivel})"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(nome={self._nome!r}, nivel={self._nivel})"

# Subclasse Striker de Lutador
class Striker(Lutador):
   
  
    #Caps altos em Boxe, Muay Thai, Capoeira e Karatê.
    #Caps baixos em artes de grappling.
    

    def _caps(self) -> dict[str, int]:
        return CAPS_STRIKER

    def atacar(self, alvo: "Lutador", arte: str) -> str:
       
        if not self.arte_desbloqueada(arte):
            raise NivelInsuficienteError(f"{arte} não está desbloqueada.")

        nivel_arte = self.nivel_arte(arte)

        # Custo de stamina e dano por arte
        custos = {
            "boxe":       10,
            "muay_thai":  15,
            "capoeira":   18,
            "karate":     12,
            "jiu_jitsu":  20,
            "judo":       20,
            "luta_livre": 18,
            "wrestling":  16,
        }

        self.consumir_stamina(custos[arte])

        # Dano: força + nível da arte + bônus de 20% se for arte de striking
        bonus = 1.2 if arte in ARTES_STRIKING else 0.8
        dano = int((self._forca + nivel_arte * 2) * bonus)

        return dano, f"{self._nome} usou {arte.replace('_',' ').title()} causando {dano} de dano!"



# Subclasse Grappler
class Grappler(Lutador):
    """
    Caps altos em Jiu-Jitsu, Judô, Luta Livre e Wrestling.
    Caps baixos em artes de striking.
    """

    def _caps(self) -> dict[str, int]:
        return CAPS_GRAPPLER

    def atacar(self, alvo: "Lutador", arte: str) -> str:
        if not self.arte_desbloqueada(arte):
            raise NivelInsuficienteError(f"{arte} não está desbloqueada.")

        nivel_arte = self.nivel_arte(arte)

        custos = {
            "boxe":       12,
            "muay_thai":  16,
            "capoeira":   18,
            "karate":     14,
            "jiu_jitsu":  14,
            "judo":       16,
            "luta_livre": 15,
            "wrestling":  13,
        }

        self.consumir_stamina(custos[arte])

        # Dano: resistência + nível da arte + bônus de 20% se for arte de grappling
        bonus = 1.2 if arte in ARTES_GRAPPLING else 0.8
        dano = int((self._resistencia + nivel_arte * 2) * bonus)

        return dano, f"{self._nome} aplicou {arte.replace('_',' ').title()} causando {dano} de dano!"
