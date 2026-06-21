"""
RPG TITULO
Módulo: menu.py
Interface CLI completa com save/load JSON.
"""

import json
import os
import sys

from personagem import (
    CLASSES_DISPONIVEIS, criar_personagem,
    carregar_personagem, PersonagemMixin,
)
from combate import Combate
from lutador import (
    TODAS_AS_ARTES, NIVEL_DESBLOQUEIO,
    NivelInsuficienteError, CapAtingidoError, AtributoInvalidoError,
)

ARQUIVO_SAVE = "save.json"

# Utilitários de terminal

def limpar():
    os.system("cls" if os.name == "nt" else "clear")

def pausar():
    input("\n  Pressione Enter para continuar...")

def titulo(texto: str):
    print(f"\n{'═' * 55}")
    print(f"  {texto}")
    print(f"{'═' * 55}")

def opcao(numero: str, texto: str):
    print(f"  [{numero}] {texto}")

def ler_int(prompt: str, minimo: int, maximo: int) -> int:
    while True:
        try:
            valor = int(input(f"  {prompt} ({minimo}-{maximo}): "))
            if minimo <= valor <= maximo:
                return valor
            print(f"Digite um valor entre {minimo} e {maximo}.")
        except ValueError:
            print("Digite um número válido.")

def ler_opcao(validas: list[str], prompt: str = "Escolha") -> str:
    while True:
        entrada = input(f"\n  {prompt} > ").strip()
        if entrada in validas:
            return entrada
        print(f"Opção inválida. Escolha entre: {', '.join(validas)}")


# Save / Load
def salvar_jogo(personagens: list) -> bool:
    try:
        dados = [p.para_dict() for p in personagens]
        with open(ARQUIVO_SAVE, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        print(f"\n Jogo salvo em '{ARQUIVO_SAVE}'.")
        return True
    except Exception as e:
        print(f"\nErro ao salvar: {e}")
        return False

def carregar_jogo() -> list:
    if not os.path.exists(ARQUIVO_SAVE):
        return []
    try:
        with open(ARQUIVO_SAVE, "r", encoding="utf-8") as f:
            dados = json.load(f)
        personagens = [carregar_personagem(d) for d in dados]
        print(f"\n{len(personagens)} personagem(ns) carregado(s).")
        return personagens
    except Exception as e:
        print(f"\nErro ao carregar save: {e}")
        return []

# Criação de personagem
def tela_criar_personagem() -> PersonagemMixin | None:
    limpar()
    titulo("CRIAR NOVO PERSONAGEM")

    # Nome
    nome = input("  Nome do personagem: ").strip()
    if not nome:
        print("Nome não pode ser vazio.")
        pausar()
        return None

    # Escolha de classe
    print("\n  Escolha a classe:\n")
    classes = list(CLASSES_DISPONIVEIS.keys())
    descricoes = {
        "Boxeador":        "Striker — Especialista em boxe. Alto dano, veloz.",
        "MuayThaiLutador": "Striker — Resistente, brutal no clinch e nos chutes.",
        "Capoeirista":     "Striker — Ágil e imprevisível. Alta esquiva.",
        "AtletaJJ":        "Grappler — Mestre em finalizações no chão.",
        "Judoca":          "Grappler — Explosivo nas quedas e no controle.",
        "LutadorLivre":    "Grappler — Versátil entre o chão e em pé.",
    }
    for i, cls in enumerate(classes, 1):
        print(f"  [{i}] {cls:18} — {descricoes[cls]}")

    escolha = ler_int("Classe", 1, len(classes))
    classe_nome = classes[escolha - 1]

    # Distribuição de atributos (pontos livres)
    print("\n  Distribua 10 pontos entre os atributos (base 5 em cada):")
    pontos = 10
    forca = resistencia = agilidade = 5

    for attr_nome in ["Força", "Resistência", "Agilidade"]:
        if pontos == 0:
            break
        print(f"  Pontos restantes: {pontos}")
        gasto = ler_int(f"  Pontos em {attr_nome}", 0, min(pontos, 15))
        if attr_nome == "Força":
            forca += gasto
        elif attr_nome == "Resistência":
            resistencia += gasto
        else:
            agilidade += gasto
        pontos -= gasto

    try:
        p = criar_personagem(
            classe_nome, nome,
            forca=forca,
            resistencia=resistencia,
            agilidade=agilidade,
        )
        limpar()
        titulo(f"PERSONAGEM CRIADO")
        print(p.status_completo())
        pausar()
        return p
    except Exception as e:
        print(f"\nErro ao criar personagem: {e}")
        pausar()
        return None



# Gerenciamento de personagem
def selecionar_personagem(personagens: list, prompt: str = "Selecione um personagem") -> PersonagemMixin | None:
    if not personagens:
        print("\nNenhum personagem criado ainda.")
        pausar()
        return None
    print(f"\n {prompt}:\n")
    for i, p in enumerate(personagens, 1):
        tipo = "Striker" if hasattr(p, '_caps') and 'boxe' in p._caps() and p._caps()['boxe'] == 10 else "Grappler"
        print(f"  [{i}] {p.nome:15} — {p.__class__.__name__} Nível {p.nivel}")
    opcao_volta = str(len(personagens) + 1)
    print(f"  [{opcao_volta}] Voltar")
    escolha = ler_int("Personagem", 1, len(personagens) + 1)
    if escolha == len(personagens) + 1:
        return None
    return personagens[escolha - 1]


def tela_ver_personagem(p: PersonagemMixin):
    limpar()
    titulo(f"FICHA — {p.nome}")
    print(p.status_completo())

    # Técnicas disponíveis
    print("\n  Técnicas disponíveis:\n")
    tecnicas = p.tecnicas_disponiveis()
    if not tecnicas:
        print("  Nenhuma técnica disponível no momento.")
    else:
        for arte, lista in tecnicas.items():
            print(f"  {'🔵' if arte in ['boxe','muay_thai','capoeira','karate'] else '🟤'} "
                  f"{arte.replace('_',' ').title()}")
            for t in lista:
                print(f"    • {t['nome']:20} Custo: {t['custo']} ST  Mult: x{t['mult']:.1f}")
    pausar()


def tela_academia(p: PersonagemMixin, personagens: list):
    #Permite treinar atributos físicos ou artes marciais.
    while True:
        limpar()
        titulo(f"ACADEMIA — {p.nome}")
        print(p.status_completo())
        print()
        opcao("1", "Academia de Condicionamento (atributos físicos)")
        opcao("2", "Academia de Arte Marcial")
        opcao("0", "Voltar")

        escolha = ler_opcao(["1", "2", "0"])

        if escolha == "0":
            break

        elif escolha == "1":
            tela_condicionar(p, personagens)

        elif escolha == "2":
            tela_treinar_arte(p, personagens)


def tela_condicionar(p: PersonagemMixin, personagens: list):
    limpar()
    titulo("CONDICIONAMENTO FÍSICO")
    print(f"  Força: {p.forca}  Resistência: {p.resistencia}  Agilidade: {p.agilidade}\n")
    print("  Escolha o atributo para aumentar em +1 (custo: 50 XP simulado)\n")
    opcao("1", f"Força        (atual: {p.forca})")
    opcao("2", f"Resistência  (atual: {p.resistencia})")
    opcao("3", f"Agilidade    (atual: {p.agilidade})")
    opcao("0", "Voltar")

    escolha = ler_opcao(["1", "2", "3", "0"])
    if escolha == "0":
        return

    try:
        if escolha == "1":
            p.forca += 1
            print(f"\n Força aumentada para {p.forca}!")
        elif escolha == "2":
            p.resistencia += 1
            print(f"\nResistência aumentada para {p.resistencia}!")
        elif escolha == "3":
            p.agilidade += 1
            print(f"\nAgilidade aumentada para {p.agilidade}!")
        salvar_jogo(personagens)
    except AtributoInvalidoError as e:
        print(f"\n {e}")
    pausar()


def tela_treinar_arte(p: PersonagemMixin, personagens: list):
    limpar()
    titulo("TREINAR ARTE MARCIAL")
    caps = p._caps()

    print("  Artes disponíveis:\n")
    artes_mostrar = []
    for arte in TODAS_AS_ARTES:
        nivel_atual = p.nivel_arte(arte)
        nivel_req   = NIVEL_DESBLOQUEIO[arte]
        cap         = caps[arte]
        bloqueada   = nivel_atual == 0
        no_cap      = nivel_atual >= cap

        status = ""
        if bloqueada:
            status = f"Requer nível {nivel_req}"
        elif no_cap:
            status = f"Cap atingido ({cap})"
        else:
            status = f"lv.{nivel_atual}/{cap}"

        artes_mostrar.append((arte, status, bloqueada or no_cap))
        print(f"  [{len(artes_mostrar):2}] {arte.replace('_',' ').title():18} {status}")

    opcao_volta = str(len(artes_mostrar) + 1)
    print(f"  [{opcao_volta}] Voltar")

    escolha = ler_int("Arte", 1, len(artes_mostrar) + 1)
    if escolha == len(artes_mostrar) + 1:
        return

    arte_escolhida, _, indisponivel = artes_mostrar[escolha - 1]

    try:
        p.treinar_arte(arte_escolhida)
        salvar_jogo(personagens)
    except (NivelInsuficienteError, CapAtingidoError) as e:
        print(f"\n {e}")
    pausar()

# Combate interativo
def tela_combate(personagens: list):
    limpar()
    titulo("BATALHA")
    opcao("1", "Jogador vs Bot")
    opcao("2", "Jogador vs Jogador")
    opcao("0", "Voltar")

    modo = ler_opcao(["1", "2", "0"])
    if modo == "0":
        return

    # Seleciona lutador 1
    print("\n  — Lutador 1 —")
    l1 = selecionar_personagem(personagens, "Selecione o Lutador 1")
    if not l1:
        return

    if modo == "2":
        print("\n  — Lutador 2 —")
        l2 = selecionar_personagem(personagens, "Selecione o Lutador 2")
        if not l2 or l2 is l1:
            print("\nSelecione um personagem diferente para o Lutador 2.")
            pausar()
            return
    else:
        # Cria um bot da classe oposta
        from personagem import Boxeador, AtletaJJ
        from lutador import Striker
        if isinstance(l1, Striker):
            l2 = AtletaJJ("BOT Grappler", forca=l1.forca, resistencia=l1.resistencia, agilidade=l1.agilidade)
        else:
            l2 = Boxeador("BOT Striker", forca=l1.forca, resistencia=l1.resistencia, agilidade=l1.agilidade)
        print(f"\nOponente: {l2.nome} ({l2.__class__.__name__})")
        pausar()

    # Configura número máximo de rounds
    print("\n  Configuração da luta:")
    rounds_max = ler_int("Número máximo de rounds", 1, 10)

    # Loop de combate
    combate = Combate(l1, l2, rounds_max=rounds_max)
    turno_jogador = 1 if modo == "2" else 0   # no PvP ambos são jogadores

    while not combate.encerrado:

        # ── Intervalo de round
        if combate.round_encerrado:
            limpar()
            combate.encerrar_round()   # recupera stamina, avança round e verifica limite

            # Se o limite de rounds foi atingido, encerrar_round já marcou encerrado
            if combate.encerrado:
                break

            titulo(f"FIM DO ROUND {combate.round - 1}  —  INTERVALO NO CORNER")
            print(f"\n  Rounds disputados: {combate.round - 1}/{combate.rounds_max}")
            print(f"\n  {l1.nome:20} HP {l1.hp}/{l1.hp_max}  ST {l1.stamina}/{l1.stamina_max}")
            print(f"  {l2.nome:20} HP {l2.hp}/{l2.hp_max}  ST {l2.stamina}/{l2.stamina_max}")

            print(f"\n  O que o corner de {l1.nome} decide?\n")
            opcao("1", f"Continuar luta  →  Round {combate.round}")
            opcao("2", f"Jogar a toalha  →  {l2.nome} vence por TKO")

            decisao = ler_opcao(["1", "2"])
            if decisao == "2":
                combate.jogar_toalha(l1)
                break

            # No modo PvP o segundo corner também decide
            if modo == "2":
                print(f"\n  O que o corner de {l2.nome} decide?\n")
                opcao("1", f"Continuar luta  →  Round {combate.round}")
                opcao("2", f"Jogar a toalha  →  {l1.nome} vence por TKO")

                decisao2 = ler_opcao(["1", "2"])
                if decisao2 == "2":
                    combate.jogar_toalha(l2)
                    break

            print(f"\nRound {combate.round} começa!")
            pausar()
            continue

        #Turno normal
        limpar()
        combate.exibir_estado()

        ativo = combate.ativo
        eh_bot = (modo == "1" and ativo is l2)

        if eh_bot:
            print(f"\n  🤖 Turno do BOT ({ativo.nome})...")
            pausar()
            combate.turno_bot()
            continue

        # Turno do jogador
        print(f"\n  O que {ativo.nome} vai fazer?\n")
        opcao("1", "Atacar")
        opcao("2", "Defender")
        opcao("3", "Recuperar Stamina")
        opcao("0", "Encerrar combate (desistir)")

        acao = ler_opcao(["1", "2", "3", "0"])

        if acao == "0":
            print(f"\n  🏳️  {ativo.nome} desistiu!")
            combate._encerrado = True
            combate._vencedor  = combate.passivo
            break

        elif acao == "2":
            combate.acao_defender()

        elif acao == "3":
            combate.acao_recuperar_stamina()

        elif acao == "1":
            limpar()
            combate.exibir_estado()
            print(f"\n  Técnicas de {ativo.nome}:\n")
            opcoes_tecnicas = combate.exibir_tecnicas_disponiveis()

            if not opcoes_tecnicas:
                print("\nSem técnicas disponíveis! Recuperando stamina automaticamente.")
                pausar()
                combate.acao_recuperar_stamina()
                continue

            validas = list(opcoes_tecnicas.keys()) + ["0"]
            opcao("0", "Voltar (escolher outra ação)")
            escolha_tec = ler_opcao(validas)

            if escolha_tec == "0":
                continue

            arte, idx = opcoes_tecnicas[escolha_tec]
            combate.acao_atacar(arte, idx)

        pausar()

    # Fim do combate
    limpar()
    combate.resumo_final()

    # Salva se foi modo vs bot (o personagem do jogador ganhou XP)
    if modo == "1":
        salvar_jogo(personagens)

    pausar()



# Menu principal
def menu_personagem(personagens: list):
    while True:
        limpar()
        titulo("GERENCIAR PERSONAGEM")
        opcao("1", "Ver ficha completa")
        opcao("2", "Ir para a Academia")
        opcao("3", "Dar XP (simulação de treino)")
        opcao("0", "Voltar")

        esc = ler_opcao(["1", "2", "3", "0"])
        if esc == "0":
            break

        p = selecionar_personagem(personagens)
        if not p:
            continue

        if esc == "1":
            tela_ver_personagem(p)
        elif esc == "2":
            tela_academia(p, personagens)
        elif esc == "3":
            limpar()
            titulo(f"DAR XP — {p.nome}")
            xp = ler_int("Quantidade de XP", 1, 9999)
            p.ganhar_xp(xp)
            salvar_jogo(personagens)
            pausar()


def menu_principal():
    personagens: list[PersonagemMixin] = []

    # Carrega save se existir
    limpar()
    titulo("RPG UFC")
    print("  Bem-vindo ao UFC!\n")

    if os.path.exists(ARQUIVO_SAVE):
        resp = input("  Save encontrado. Carregar? [s/n]: ").strip().lower()
        if resp == "s":
            personagens = carregar_jogo()

    pausar()

    while True:
        limpar()
        titulo("=-=-=-UFC-=-=-=")
        print(f"  Personagens carregados: {len(personagens)}\n")
        opcao("1", "Criar personagem")
        opcao("2", "Gerenciar personagem")
        opcao("3", "Batalhar")
        opcao("4", "Listar personagens")
        opcao("5", "Salvar jogo")
        opcao("0", "Sair")

        esc = ler_opcao(["1", "2", "3", "4", "5", "0"])

        if esc == "0":
            salvar_jogo(personagens)
            print("\n  Até a próxima!")
            sys.exit(0)

        elif esc == "1":
            p = tela_criar_personagem()
            if p:
                personagens.append(p)
                salvar_jogo(personagens)

        elif esc == "2":
            menu_personagem(personagens)

        elif esc == "3":
            if len(personagens) == 0:
                print("\nCrie pelo menos um personagem antes de batalhar.")
                pausar()
            else:
                tela_combate(personagens)

        elif esc == "4":
            limpar()
            titulo("PERSONAGENS")
            if not personagens:
                print("  Nenhum personagem criado ainda.")
            else:
                for p in personagens:
                    print(f"  • {p.nome:15} {p.__class__.__name__:18} Nível {p.nivel}  HP {p.hp}/{p.hp_max}")
            pausar()

        elif esc == "5":
            salvar_jogo(personagens)
            pausar()

#main
if __name__ == "__main__":
    menu_principal()
