"""
RPG Manager — MMA Edition
Módulo: combate.py
Sistema de batalha por turnos entre dois personagens.
"""

import random
from personagem import PersonagemMixin, TECNICAS
from lutador import (
    Lutador, Striker, Grappler,
    ARTES_STRIKING, ARTES_GRAPPLING,
    StaminaInsuficienteError, NivelInsuficienteError,
)


# Exceção de combate
class CombateEncerradoError(Exception):
    """Lançada quando se tenta agir num combate já finalizado."""
    pass


# Ações possíveis num turno
ACOES = {
    "1": "atacar",
    "2": "defender",
    "3": "recuperar_stamina",
}



# Classe principal de Combate
class Combate:
    """
    Gerencia uma batalha por turnos entre dois personagens.

    Fluxo de um turno:
      1. Verifica se o combate acabou
      2. Ativo escolhe ação (atacar / defender / recuperar stamina)
      3. Ação é processada e logada
      4. Verifica KO
      5. Troca de turno
    """

    RECUPERACAO_STAMINA_POR_TURNO = 15   # stamina recuperada ao descansar
    RECUPERACAO_DEFESA_DANO       = 0.4  # defesa absorve 40% do dano
    XP_POR_VITORIA                = 80
    XP_POR_DERROTA                = 30
    TURNOS_POR_ROUND              = 4    # a cada 4 turnos encerra um round
    RECUPERACAO_STAMINA_CORNER    = 20   # stamina recuperada no intervalo do round

    def __init__(self, lutador1: PersonagemMixin, lutador2: PersonagemMixin,
                 rounds_max: int = 3):
        if not isinstance(lutador1, PersonagemMixin) or not isinstance(lutador2, PersonagemMixin):
            raise TypeError("Ambos os lutadores precisam ser PersonagemMixin.")
        if rounds_max < 1:
            raise ValueError("O número máximo de rounds deve ser pelo menos 1.")

        self._l1         = lutador1
        self._l2         = lutador2
        self._rounds_max     = rounds_max
        self._turno          = 1
        self._ativo          = lutador1   # quem age neste turno
        self._passivo        = lutador2   # quem recebe a ação
        self._defendendo     = False      # se o passivo está em postura defensiva
        self._log: list[str] = []
        self._encerrado      = False
        self._vencedor       = None
        self._round          = 1
        self._round_encerrado = False     # sinaliza para o menu que o round fechou

        # Restaura HP e stamina antes da luta
        self._l1.recuperar_stamina_total()
        self._l2.recuperar_stamina_total()
        if hasattr(self._l1, '_hp'):
            self._l1._hp    = self._l1.hp_max
            self._l1._vivo  = True
        if hasattr(self._l2, '_hp'):
            self._l2._hp    = self._l2.hp_max
            self._l2._vivo  = True

    #Propriedades públicas
    @property
    def rounds_max(self) -> int:
        return self._rounds_max

    @property
    def turno(self) -> int:
        return self._turno

    @property
    def ativo(self):
        return self._ativo

    @property
    def passivo(self):
        return self._passivo

    @property
    def encerrado(self) -> bool:
        return self._encerrado

    @property
    def vencedor(self):
        return self._vencedor

    @property
    def log(self) -> list[str]:
        return list(self._log)

    @property
    def round(self) -> int:
        return self._round

    @property
    def round_encerrado(self) -> bool:
        return self._round_encerrado

    #Log interno
    def _registrar(self, mensagem: str):
        entrada = f"[Turno {self._turno:02d}] {mensagem}"
        self._log.append(entrada)
        print(entrada)

    def _separador(self):
        linha = f"\n{'─' * 55}"
        self._log.append(linha)
        print(linha)

    #Verificação de fim de combate
    def _verificar_ko(self) -> bool:
        """Verifica se alguém foi nocauteado e encerra o combate."""
        for lutador, outro in [(self._l1, self._l2), (self._l2, self._l1)]:
            if lutador.esta_ko():
                self._encerrado = True
                self._vencedor  = outro
                self._registrar(
                    f"🏆 {outro.nome} vence por nocaute sobre {lutador.nome}!"
                )
                self._distribuir_xp(vencedor=outro, perdedor=lutador)
                return True
        return False

    def _verificar_stamina_zerada(self) -> bool:
        """Se ambos ficarem sem stamina, quem tem mais HP vence."""
        l1_sem = self._l1.stamina == 0
        l2_sem = self._l2.stamina == 0
        if l1_sem and l2_sem:
            self._encerrado = True
            if self._l1.hp >= self._l2.hp:
                self._vencedor = self._l1
                perdedor = self._l2
            else:
                self._vencedor = self._l2
                perdedor = self._l1
            self._registrar(
                f"😮‍💨 Ambos exaustos! {self._vencedor.nome} vence por HP ({self._vencedor.hp} vs {perdedor.hp})."
            )
            self._distribuir_xp(vencedor=self._vencedor, perdedor=perdedor)
            return True
        return False

    def _verificar_limite_rounds(self) -> bool:
        """
        Verifica se o limite máximo de rounds foi atingido.
        Em caso positivo, encerra o combate por decisão dos juízes:
          - Maior HP vence.
          - HP igual → empate (sem vencedor definido).
        Chamado por encerrar_round() após avançar o contador de rounds.
        """
        if self._round <= self._rounds_max:
            return False

        self._encerrado = True

        if self._l1.hp > self._l2.hp:
            self._vencedor = self._l1
            perdedor = self._l2
            self._registrar(
                f"📋 Decisão dos juízes após {self._rounds_max} round(s)! "
                f"{self._vencedor.nome} vence com {self._vencedor.hp} HP "
                f"contra {perdedor.hp} HP de {perdedor.nome}."
            )
            self._distribuir_xp(vencedor=self._vencedor, perdedor=perdedor)

        elif self._l2.hp > self._l1.hp:
            self._vencedor = self._l2
            perdedor = self._l1
            self._registrar(
                f"Decisão dos juízes após {self._rounds_max} round(s)! "
                f"{self._vencedor.nome} vence com {self._vencedor.hp} HP "
                f"contra {perdedor.hp} HP de {perdedor.nome}."
            )
            self._distribuir_xp(vencedor=self._vencedor, perdedor=perdedor)

        else:
            self._vencedor = None   # empate: sem vencedor
            self._registrar(
                f"Empate por decisão após {self._rounds_max} round(s)! "
                f"Ambos com {self._l1.hp} HP."
            )
            self._l1.ganhar_xp(self.XP_POR_DERROTA)
            self._l2.ganhar_xp(self.XP_POR_DERROTA)
            self._registrar(
                f"XP: {self._l1.nome} +{self.XP_POR_DERROTA} | "
                f"{self._l2.nome} +{self.XP_POR_DERROTA}"
            )

        return True

    def _distribuir_xp(self, vencedor, perdedor):
        vencedor.ganhar_xp(self.XP_POR_VITORIA)
        perdedor.ganhar_xp(self.XP_POR_DERROTA)
        self._registrar(
            f"XP: {vencedor.nome} +{self.XP_POR_VITORIA} | "
            f"{perdedor.nome} +{self.XP_POR_DERROTA}"
        )

    # ── Ações de turno ────────────────────────────────────────────────

    def acao_atacar(self, arte: str, indice_tecnica: int):
        """Ação de ataque: usa uma técnica contra o oponente."""
        if self._encerrado:
            raise CombateEncerradoError("O combate já terminou.")

        # Se o passivo estiver defendendo, reduz o dano recebido
        modo_defesa = self._defendendo

        try:
            dano_bruto, log_ataque = self._ativo.usar_tecnica(
                self._passivo, arte, indice_tecnica
            )
        except StaminaInsuficienteError as e:
            self._registrar(f"{self._ativo.nome} sem stamina! ({e})")
            self._avancar_turno()
            return
        except NivelInsuficienteError as e:
            self._registrar(f"Técnica indisponível: {e}")
            return   # não avança turno — jogador escolhe outra

        if modo_defesa:
            # Desfaz o dano já aplicado e reaplica com redução de 40%
            dano_reduzido = int(dano_bruto * (1 - self.RECUPERACAO_DEFESA_DANO))
            dano_extra    = dano_bruto - dano_reduzido
            self._passivo.curar(dano_extra)   # devolve a diferença
            self._registrar(
                f"{self._passivo.nome} estava em defesa! "
                f"Dano reduzido: {dano_bruto} → {dano_reduzido}"
            )

        self._registrar(log_ataque)
        self._defendendo = False   # defesa se consome após receber ataque

        if self._verificar_ko():
            return
        self._avancar_turno()

    def acao_defender(self):
        """Ação de defesa: o lutador se prepara para absorver o próximo ataque."""
        if self._encerrado:
            raise CombateEncerradoError("O combate já terminou.")
        self._defendendo = True
        self._registrar(f"🛡️  {self._ativo.nome} adota postura defensiva.")
        self._avancar_turno()

    def acao_recuperar_stamina(self):
        """Ação de descanso: recupera stamina mas perde o turno."""
        if self._encerrado:
            raise CombateEncerradoError("O combate já terminou.")
        recuperado = self.RECUPERACAO_STAMINA_POR_TURNO
        self._ativo.recuperar_stamina(recuperado)
        self._registrar(
            f"{self._ativo.nome} descansa e recupera {recuperado} de stamina "
            f"({self._ativo.stamina}/{self._ativo.stamina_max})."
        )
        self._avancar_turno()

    # ── Troca de turno ────────────────────────────────────────────────

    def _avancar_turno(self):
        if self._verificar_stamina_zerada():
            return
        self._turno  += 1
        self._ativo, self._passivo = self._passivo, self._ativo
        self._defendendo = False

        # Verifica se completou um round (a cada TURNOS_POR_ROUND turnos)
        if (self._turno - 1) % self.TURNOS_POR_ROUND == 0:
            self._round_encerrado = True

    def encerrar_round(self):
        """
        Chamado pelo menu ao fim de cada round.
        Recupera stamina dos dois lutadores no corner e avança o contador de round.
        Se o novo round ultrapassar rounds_max, encerra o combate por decisão.
        """
        rec = self.RECUPERACAO_STAMINA_CORNER
        self._l1.recuperar_stamina(rec)
        self._l2.recuperar_stamina(rec)
        self._round += 1
        self._round_encerrado = False
        self._separador()
        self._registrar(
            f"Fim do Round {self._round - 1}! Intervalo no corner. "
            f"Cada lutador recupera {rec} de stamina."
        )
        self._registrar(
            f"   {self._l1.nome}: ST {self._l1.stamina}/{self._l1.stamina_max}  |  "
            f"{self._l2.nome}: ST {self._l2.stamina}/{self._l2.stamina_max}"
        )
        self._separador()

        # Verifica se o limite de rounds foi atingido
        self._verificar_limite_rounds()

    def jogar_toalha(self, lutador: PersonagemMixin):
        """
        Encerra o combate por desistência do corner do lutador informado.
        O adversário vence por TKO (toalha).
        """
        if self._encerrado:
            raise CombateEncerradoError("O combate já terminou.")

        vencedor = self._l2 if lutador is self._l1 else self._l1
        self._encerrado      = True
        self._vencedor       = vencedor
        self._round_encerrado = False
        self._registrar(
            f"Corner de {lutador.nome} jogou a toalha! "
            f"{vencedor.nome} vence por TKO!"
        )
        self._distribuir_xp(vencedor=vencedor, perdedor=lutador)

    # ── Exibição do estado atual ──────────────────────────────────────

    def exibir_estado(self):
        turno_no_round = ((self._turno - 1) % self.TURNOS_POR_ROUND) + 1
        print(f"\n{'═' * 55}")
        print(f"  ROUND {self._round}  —  TURNO {turno_no_round}/{self.TURNOS_POR_ROUND}  —  Vez de: {self._ativo.nome}")
        print(f"{'═' * 55}")
        print(f"  {self._l1.nome:20} {self._l1.barra_hp()}")
        print(f"  {' ':20} {self._l1.barra_stamina()}")
        print()
        print(f"  {self._l2.nome:20} {self._l2.barra_hp()}")
        print(f"  {' ':20} {self._l2.barra_stamina()}")
        print(f"{'─' * 55}")

    def exibir_tecnicas_disponiveis(self):
        """Mostra o menu de técnicas do lutador ativo."""
        tecnicas = self._ativo.tecnicas_disponiveis()
        if not tecnicas:
            print("Nenhuma técnica disponível!")
            return {}

        opcoes = {}   # índice_global -> (arte, índice_local)
        contador = 1

        for arte, lista in tecnicas.items():
            tipo = "🔵" if arte in ARTES_STRIKING else "🟤"
            print(f"\n  {tipo} {arte.replace('_', ' ').title()} (lv.{self._ativo.nivel_arte(arte)})")
            for i, t in enumerate(lista):
                print(
                    f"    [{contador}] {t['nome']:20} "
                    f"Custo: {t['custo']} ST  "
                    f"Mult: x{t['mult']:.1f}"
                )
                opcoes[str(contador)] = (arte, i)
                contador += 1

        return opcoes

    # ── Turno controlado pelo bot ─────────────────────────────────────

    def turno_bot(self):
        """
        IA simples para o modo jogador vs bot.
        Estratégia: se stamina < 25 descansa; senão usa a técnica mais forte disponível.
        """
        if self._encerrado:
            return

        # Recupera stamina se estiver baixa
        if self._ativo.stamina < 25:
            self.acao_recuperar_stamina()
            return

        # Escolhe a melhor técnica disponível (maior multiplicador)
        tecnicas = self._ativo.tecnicas_disponiveis()
        if not tecnicas:
            self.acao_recuperar_stamina()
            return

        melhor_arte    = None
        melhor_indice  = 0
        melhor_mult    = 0.0

        for arte, lista in tecnicas.items():
            for i, t in enumerate(lista):
                if t["custo"] <= self._ativo.stamina and t["mult"] > melhor_mult:
                    melhor_arte   = arte
                    melhor_indice = i
                    melhor_mult   = t["mult"]

        if melhor_arte:
            # 20% de chance de defender em vez de atacar
            if random.random() < 0.2:
                self.acao_defender()
            else:
                self.acao_atacar(melhor_arte, melhor_indice)
        else:
            self.acao_recuperar_stamina()

    # ── Resumo final ──────────────────────────────────────────────────

    def resumo_final(self):
        if not self._encerrado:
            print("O combate ainda não terminou.")
            return
        print(f"\n{'═' * 55}")
        print(f"  FIM DE COMBATE — Round {self._round}  |  {self._turno - 1} turno(s) no total")
        print(f"{'═' * 55}")
        if self._vencedor:
            print(f"Vencedor: {self._vencedor.nome}")
        else:
            print(f"Resultado: EMPATE")
        print(f"\n  Estado final:")
        print(f"    {self._l1.nome}: HP {self._l1.hp}/{self._l1.hp_max}  "
              f"ST {self._l1.stamina}/{self._l1.stamina_max}")
        print(f"    {self._l2.nome}: HP {self._l2.hp}/{self._l2.hp_max}  "
              f"ST {self._l2.stamina}/{self._l2.stamina_max}")
        print(f"{'═' * 55}\n")
