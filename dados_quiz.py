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

    # ========================================================
    # VÍDEO 1 — UMA IMAGEM ÚNICA EM CADA PERGUNTA
    # ========================================================
    "Desafio Visual": [
        {
            "pergunta": "Qual destes animais é um mamífero marinho?",
            "alternativas": ["Tubarão", "Golfinho", "Pinguim"],
            "correta": 1,
            "imagem": "imagens_perguntas/desafio_01.png",
        },
        {
            "pergunta": "Qual destes monumentos fica na Itália?",
            "alternativas": ["Coliseu", "Big Ben", "Torre Eiffel"],
            "correta": 0,
            "imagem": "imagens_perguntas/desafio_02.png",
        },
        {
            "pergunta": "Qual destes alimentos é produzido pelas abelhas?",
            "alternativas": ["Geleia", "Xarope", "Mel"],
            "correta": 2,
            "imagem": "imagens_perguntas/desafio_03.png",
        },
    ],

    # ========================================================
    # VÍDEO 2 — SEM IMAGENS
    # ========================================================
    "Mistérios do Corpo": [
        {
            "pergunta": "Qual parte do corpo humano não possui vasos sanguíneos?",
            "alternativas": ["Córnea", "Tímpano", "Unha"],
            "correta": 0,
        },
        {
            "pergunta": "Qual órgão produz a maior parte da bile?",
            "alternativas": ["Pâncreas", "Fígado", "Baço"],
            "correta": 1,
        },
        {
            "pergunta": "Qual estrutura protege o cérebro dentro da cabeça?",
            "alternativas": ["Esterno", "Escápula", "Crânio"],
            "correta": 2,
        },
    ],

    # ========================================================
    # VÍDEO 3 — SEM IMAGENS
    # ========================================================
    "Curiosidades do Planeta": [
        {
            "pergunta": "Qual é o maior oceano da Terra?",
            "alternativas": ["Pacífico", "Atlântico", "Índico"],
            "correta": 0,
        },
        {
            "pergunta": "Qual camada da Terra é formada principalmente por ferro e níquel?",
            "alternativas": ["Crosta", "Núcleo", "Manto"],
            "correta": 1,
        },
        {
            "pergunta": "Qual continente possui a maior quantidade de países?",
            "alternativas": ["Europa", "Ásia", "África"],
            "correta": 2,
        },
    ],

}
