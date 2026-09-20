# ============================================================
# JUH QUIZ — PINCÉIS DE 5 CORES
#
# Cada tema gera 1 vídeo.
# correta: 0=A, 1=B, 2=C
#
# As cores são automáticas por vídeo:
# 1 rosa | 2 verde | 3 amarelo | 4 azul | 5 roxo
# 6 rosa novamente e assim por diante.
# ============================================================

QUIZZES = {
    "Conhecimentos Gerais": [
        {
            "pergunta": "Qual é a capital do Brasil?",
            "alternativas": ["Rio de Janeiro", "Brasília", "São Paulo"],
            "correta": 1,
        },
        {
            "pergunta": "Qual planeta é conhecido como Planeta Vermelho?",
            "alternativas": ["Terra", "Marte", "Júpiter"],
            "correta": 1,
        },
        {
            "pergunta": "Qual é o maior oceano do mundo?",
            "alternativas": ["Atlântico", "Índico", "Pacífico"],
            "correta": 2,
        },
        {
            "pergunta": "Quantos lados tem um triângulo?",
            "alternativas": ["3", "4", "5"],
            "correta": 0,
        },
        {
            "pergunta": "Qual gás utilizamos na respiração?",
            "alternativas": ["Oxigênio", "Nitrogênio", "Hélio"],
            "correta": 0,
        },
    ],

    "Corpo Humano": [
        {
            "pergunta": "Qual órgão bombeia o sangue por todo o corpo?",
            "alternativas": ["Pulmão", "Coração", "Fígado"],
            "correta": 1,
        },
        {
            "pergunta": "Quantos ossos tem, em geral, o corpo humano adulto?",
            "alternativas": ["206", "186", "226"],
            "correta": 0,
        },
        {
            "pergunta": "Qual órgão é responsável principalmente pelas trocas gasosas?",
            "alternativas": ["Pulmões", "Rins", "Estômago"],
            "correta": 0,
        },
    ],

    "Matemática": [
        {
            "pergunta": "Quanto é 80 mais 20 dividido por 2?",
            "alternativas": ["90", "50", "100"],
            "correta": 0,
        },
        {
            "pergunta": "Quantos minutos existem em 2 horas?",
            "alternativas": ["60", "100", "120"],
            "correta": 2,
        },
        {
            "pergunta": "Quanto é 9 vezes 7?",
            "alternativas": ["56", "63", "72"],
            "correta": 1,
        },
    ],

    "Português": [
        {
            "pergunta": "Qual palavra é um substantivo?",
            "alternativas": ["Correr", "Casa", "Bonito"],
            "correta": 1,
        },
        {
            "pergunta": "Qual é o plural de papel?",
            "alternativas": ["Papéis", "Papels", "Papeles"],
            "correta": 0,
        },
        {
            "pergunta": "Qual palavra está escrita corretamente?",
            "alternativas": ["Exceção", "Excessão", "Eceção"],
            "correta": 0,
        },
    ],

    "Ciências": [
        {
            "pergunta": "Em condições comuns, a água congela a quantos graus Celsius?",
            "alternativas": ["0", "10", "20"],
            "correta": 0,
        },
        {
            "pergunta": "Qual estrela ilumina a Terra?",
            "alternativas": ["Lua", "Sol", "Vênus"],
            "correta": 1,
        },
        {
            "pergunta": "Qual destes animais é mamífero?",
            "alternativas": ["Golfinho", "Tubarão", "Sardinha"],
            "correta": 0,
        },
    ],

    # O sexto vídeo volta automaticamente para o pincel ROSA.
    "Geografia": [
        {
            "pergunta": "Qual é o maior país da América do Sul em área?",
            "alternativas": ["Brasil", "Argentina", "Peru"],
            "correta": 0,
        },
        {
            "pergunta": "Em qual continente fica o Egito?",
            "alternativas": ["África", "Europa", "Ásia"],
            "correta": 0,
        },
        {
            "pergunta": "Qual é a capital da França?",
            "alternativas": ["Roma", "Paris", "Madri"],
            "correta": 1,
        },
    ],
}
