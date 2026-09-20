JUH QUIZ — 5 PINCÉIS
=====================

NOVO MODELO
-----------
Cada vídeo usa apenas UMA cor de pincel.

Ordem automática:
1 - rosa
2 - verde
3 - amarelo
4 - azul
5 - roxo
6 - rosa novamente
7 - verde novamente
... e assim por diante.

A mão e o risco usam a mesma cor.

ARQUIVOS PRINCIPAIS
-------------------
gerar_videos_juh_pinceis.py
dados_quiz.py
requirements.txt

assets/
  fundo_folha_juh_quiz.png
  mao_rosa.png
  mao_verde.png
  mao_amarelo.png
  mao_azul.png
  mao_roxo.png

.github/workflows/
  gerar-juh-quiz-pinceis.yml

COMO USAR
---------
1. Crie um repositório novo no GitHub.
2. Envie todos os arquivos mantendo as pastas.
3. Edite apenas dados_quiz.py para criar os vídeos.
4. Vá em Actions.
5. Abra "Gerar Juh Quiz - 5 Pinceis".
6. Clique em Run workflow.
7. Baixe o Artifact.

PREVIEW
-------
python gerar_videos_juh_pinceis.py --preview

O preview cria 5 imagens, uma para cada pincel.

REGRAS
------
- 1 tema = 1 vídeo
- até 5 perguntas por vídeo
- correta: 0=A, 1=B, 2=C
- voz masculina
- lê somente a pergunta
- não lê as alternativas
- contagem 3,2,1
- depois lê somente a resposta correta
