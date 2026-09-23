import math
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter
from dados_quiz import QUIZZES

# ============================================================
# CONFIGURAÇÕES
# ============================================================

W = 1080
H = 1920
FPS = 30
ANIM_FPS = 20

VOZ = "pt-BR-AntonioNeural"
VELOCIDADE_VOZ = "+10%"

AUDIO_HZ = 48000
AUDIO_CHANNELS = 2

PAUSA_DEPOIS_PERGUNTA = 0.10
PAUSA_DEPOIS_RESPOSTA = 0.55

FUNDO = Path("assets/fundo_folha_juh_quiz.png")
IMAGENS_OPCOES_DIR = Path("imagens_opcoes")
IMAGENS_PERGUNTAS_DIR = Path("imagens_perguntas")

FUSO = ZoneInfo("America/Fortaleza")
DATA_DO_DIA = datetime.now(FUSO).strftime("%Y-%m-%d")

PASTA_RAIZ = Path("output_juh_pinceis")
PASTA_TMP = Path("_tmp_juh_pinceis")
PASTA_SAIDA = PASTA_RAIZ / DATA_DO_DIA

AZUL = (13, 88, 187)
AZUL_ESCURO = (12, 39, 94)
PRETO = (20, 20, 24)
BRANCO = (255, 255, 255)

# ============================================================
# 5 PINCÉIS
# ============================================================

PINCEIS = [
    {
        "nome": "rosa",
        "mao": Path("assets/mao_rosa.png"),
        "cor": (255, 28, 153, 215),
    },
    {
        "nome": "verde",
        "mao": Path("assets/mao_verde.png"),
        "cor": (119, 236, 66, 215),
    },
    {
        "nome": "amarelo",
        "mao": Path("assets/mao_amarelo.png"),
        "cor": (255, 210, 30, 220),
    },
    {
        "nome": "azul",
        "mao": Path("assets/mao_azul.png"),
        "cor": (32, 154, 255, 210),
    },
    {
        "nome": "roxo",
        "mao": Path("assets/mao_roxo.png"),
        "cor": (161, 76, 255, 210),
    },
]


def pincel_do_video(indice_video):
    """Vídeo 1-5 usam as 5 cores. Do vídeo 6 em diante repete."""
    return PINCEIS[(indice_video - 1) % len(PINCEIS)]


# ============================================================
# UTILIDADES
# ============================================================

def slug(texto):
    txt = unicodedata.normalize("NFKD", str(texto))
    txt = "".join(c for c in txt if not unicodedata.combining(c))
    txt = re.sub(r"[^a-zA-Z0-9]+", "-", txt).strip("-").lower()
    return txt or "quiz"


def executar(cmd):
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0:
        print(p.stdout)
        print(p.stderr)
        raise RuntimeError("Falha ao executar comando.")
    return p


def fonte(tamanho, bold=False):
    candidatos = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
    ]

    for caminho in candidatos:
        try:
            return ImageFont.truetype(caminho, tamanho)
        except Exception:
            pass

    return ImageFont.load_default()


def wrap_text(draw, texto, fnt, largura):
    palavras = str(texto).split()
    if not palavras:
        return [""]

    linhas = []
    linha = palavras[0]

    for palavra in palavras[1:]:
        teste = linha + " " + palavra
        bb = draw.textbbox((0, 0), teste, font=fnt)
        if bb[2] - bb[0] <= largura:
            linha = teste
        else:
            linhas.append(linha)
            linha = palavra

    linhas.append(linha)
    return linhas


def fit_lines(draw, texto, largura, altura, max_size, min_size, max_lines, bold=True):
    for tamanho in range(max_size, min_size - 1, -2):
        fnt = fonte(tamanho, bold=bold)
        linhas = wrap_text(draw, texto, fnt, largura)

        if len(linhas) > max_lines:
            continue

        bb = draw.textbbox((0, 0), "Ag", font=fnt)
        line_h = bb[3] - bb[1]
        total_h = len(linhas) * line_h + (len(linhas) - 1) * 5

        if total_h <= altura:
            return fnt, linhas, line_h

    fnt = fonte(min_size, bold=bold)
    linhas = wrap_text(draw, texto, fnt, largura)[:max_lines]
    bb = draw.textbbox((0, 0), "Ag", font=fnt)
    return fnt, linhas, bb[3] - bb[1]


def fundo_base():
    if not FUNDO.exists():
        raise FileNotFoundError(
            f"Fundo não encontrado: {FUNDO}"
        )

    img = Image.open(FUNDO).convert("RGB")
    resampling = getattr(Image, "Resampling", Image)

    return ImageOps.fit(
        img,
        (W, H),
        method=resampling.LANCZOS,
        centering=(0.5, 0.5),
    )


def resolver_imagem_pergunta(valor):
    """Resolve uma única imagem opcional para a pergunta."""
    if valor is None:
        return None

    valor = str(valor).strip()
    if not valor:
        return None

    caminho = Path(valor)
    candidatos = [caminho]

    if not caminho.is_absolute() and caminho.parent == Path("."):
        candidatos.append(IMAGENS_PERGUNTAS_DIR / caminho)

    for candidato in candidatos:
        if candidato.exists() and candidato.is_file():
            return candidato

    tentados = ", ".join(str(c) for c in candidatos)
    raise FileNotFoundError(
        f'Imagem da pergunta não encontrada: "{valor}". '
        f'Caminhos verificados: {tentados}'
    )


def preparar_imagem_pergunta(caminho, largura=330, altura=170):
    """
    Prepara a imagem com acabamento mais limpo:
    - preenche o cartão sem faixas brancas;
    - cantos arredondados;
    - sombra suave;
    - borda fina e discreta.
    """
    resampling = getattr(Image, "Resampling", Image)
    figura = Image.open(caminho).convert("RGBA")

    # Reserva alguns pixels para a sombra, mantendo o tamanho total do cartão.
    margem_sombra = 10
    foto_w = largura - margem_sombra
    foto_h = altura - margem_sombra

    # Corta proporcionalmente para preencher todo o espaço, sem deformar.
    foto = ImageOps.fit(
        figura,
        (foto_w, foto_h),
        method=resampling.LANCZOS,
        centering=(0.5, 0.5),
    )

    card = Image.new("RGBA", (largura, altura), (0, 0, 0, 0))

    # Sombra suave: dá profundidade sem parecer um bloco branco colado na folha.
    sombra = Image.new("RGBA", (largura, altura), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sombra)
    sd.rounded_rectangle(
        [7, 8, foto_w + 7, foto_h + 8],
        radius=18,
        fill=(20, 34, 60, 52),
    )
    sombra = sombra.filter(ImageFilter.GaussianBlur(5))
    card = Image.alpha_composite(card, sombra)

    # Recorte arredondado da fotografia.
    mask = Image.new("L", (foto_w, foto_h), 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle(
        [0, 0, foto_w - 1, foto_h - 1],
        radius=17,
        fill=255,
    )
    card.paste(foto, (0, 0), mask)

    # Sem moldura branca: a fotografia chega até o recorte arredondado.
    # Mantém apenas a sombra suave para separar a imagem do fundo.
    return card


def resolver_imagem_opcao(valor):
    """
    Resolve uma imagem opcional de alternativa.

    Exemplos em dados_quiz.py:
      "imagens_opcoes": [
          "imagens_opcoes/girafa.png",
          "imagens_opcoes/elefante.png",
          "imagens_opcoes/hipopotamo.png",
      ]

    Também aceita somente o nome, como "girafa.png".
    Nesse caso procura automaticamente na pasta imagens_opcoes.
    Use None quando uma alternativa específica não tiver imagem.
    """
    if valor is None:
        return None

    valor = str(valor).strip()
    if not valor:
        return None

    caminho = Path(valor)
    candidatos = [caminho]

    if not caminho.is_absolute() and caminho.parent == Path("."):
        candidatos.append(IMAGENS_OPCOES_DIR / caminho)

    for candidato in candidatos:
        if candidato.exists() and candidato.is_file():
            return candidato

    tentados = ", ".join(str(c) for c in candidatos)
    raise FileNotFoundError(
        f'Imagem de alternativa não encontrada: "{valor}". '
        f'Caminhos verificados: {tentados}'
    )


def preparar_imagem_opcao(caminho, tamanho):
    """Encaixa a imagem em uma miniatura quadrada, sem distorcer."""
    figura = Image.open(caminho).convert("RGBA")
    resampling = getattr(Image, "Resampling", Image)
    figura.thumbnail((tamanho - 8, tamanho - 8), resampling.LANCZOS)

    thumb = Image.new("RGBA", (tamanho, tamanho), (0, 0, 0, 0))
    td = ImageDraw.Draw(thumb)
    td.rounded_rectangle(
        [0, 0, tamanho - 1, tamanho - 1],
        radius=max(6, tamanho // 6),
        fill=(255, 255, 255, 245),
        outline=(210, 218, 232, 255),
        width=2,
    )

    x = (tamanho - figura.width) // 2
    y = (tamanho - figura.height) // 2
    thumb.alpha_composite(figura, (x, y))
    return thumb


def carregar_mao(caminho):
    caminho = Path(caminho)

    if not caminho.exists():
        raise FileNotFoundError(
            f"Pincel não encontrado: {caminho}"
        )

    original = Image.open(caminho).convert("RGBA")

    # Alongamento somente do antebraço:
    # preserva mão/caneta e evita aparecer a extremidade cortada.
    w0, h0 = original.size
    split_y = int(h0 * 0.67)

    topo = original.crop((0, 0, w0, split_y))
    braco = original.crop((0, split_y, w0, h0))

    resampling = getattr(Image, "Resampling", Image)

    braco_alongado = braco.resize(
        (w0, int(braco.height * 2.45)),
        resampling.LANCZOS,
    )

    mao = Image.new(
        "RGBA",
        (w0, topo.height + braco_alongado.height),
        (0, 0, 0, 0),
    )
    mao.alpha_composite(topo, (0, 0))
    mao.alpha_composite(braco_alongado, (0, topo.height))

    largura = 610
    altura = int(mao.height * largura / mao.width)

    mao = mao.resize(
        (largura, altura),
        resampling.LANCZOS,
    )

    # Faz o final do braço "sumir" de forma suave,
    # em vez de aparecer cortado no rodapé do vídeo.
    alpha = mao.getchannel("A")
    w, h = mao.size
    px = alpha.load()

    fade_start_y = int(h * 0.72)

    for y in range(h):
        if y <= fade_start_y:
            continue

        t = (y - fade_start_y) / max(1, (h - fade_start_y))
        fator = max(0.0, 1.0 - t)

        for x in range(w):
            a = px[x, y]
            if a > 0:
                px[x, y] = int(a * fator)

    alpha = alpha.filter(ImageFilter.GaussianBlur(1.8))
    mao.putalpha(alpha)

    return mao


def validar_tema(tema, perguntas):
    if not perguntas:
        raise ValueError(f'O tema "{tema}" está sem perguntas.')

    if len(perguntas) > 5:
        raise ValueError(
            f'O tema "{tema}" tem {len(perguntas)} perguntas. '
            "Neste modelo use no máximo 5 perguntas por vídeo."
        )

    for pergunta in perguntas:
        if "pergunta" not in pergunta:
            raise ValueError(f'Pergunta sem texto no tema "{tema}".')

        if len(pergunta.get("alternativas", [])) != 3:
            raise ValueError(
                f'A pergunta "{pergunta["pergunta"]}" precisa ter 3 alternativas.'
            )

        correta = int(pergunta.get("correta", -1))
        if correta not in (0, 1, 2):
            raise ValueError(
                f'A pergunta "{pergunta["pergunta"]}" precisa de correta 0, 1 ou 2.'
            )

        imagens = pergunta.get("imagens_opcoes", pergunta.get("imagens"))
        if imagens is not None:
            if not isinstance(imagens, (list, tuple)) or len(imagens) != 3:
                raise ValueError(
                    f'A pergunta "{pergunta["pergunta"]}" precisa ter exatamente '
                    '3 itens em "imagens_opcoes" (um para A, B e C).'
                )


# ============================================================
# LAYOUT
# ============================================================

def parametros_layout(total):
    if total <= 3:
        return {
            "start_y": 535,
            "block_h": 350,
            "q_max": 46,
            "q_min": 34,
            "a_max": 37,
            "a_min": 29,
        }

    if total == 4:
        return {
            "start_y": 510,
            "block_h": 285,
            "q_max": 39,
            "q_min": 29,
            "a_max": 31,
            "a_min": 24,
        }

    return {
        "start_y": 495,
        "block_h": 235,
        "q_max": 34,
        "q_min": 26,
        "a_max": 28,
        "a_min": 22,
    }


def criar_pagina_base(tema, perguntas):
    total = len(perguntas)
    cfg = parametros_layout(total)

    img = fundo_base()
    draw = ImageDraw.Draw(img)

    # Tema
    tema_font, tema_lines, _ = fit_lines(
        draw,
        tema.upper(),
        largura=690,
        altura=70,
        max_size=43,
        min_size=25,
        max_lines=1,
        bold=True,
    )

    tema_txt = tema_lines[0] if tema_lines else tema.upper()
    bb = draw.textbbox((0, 0), tema_txt, font=tema_font)
    tw = bb[2] - bb[0]

    draw.text(
        ((W - tw) / 2, 368),
        tema_txt,
        font=tema_font,
        fill=BRANCO,
    )

    layouts = []
    x_question = 100
    x_option = 145
    right = 960

    for idx, pergunta in enumerate(perguntas, start=1):
        top = cfg["start_y"] + (idx - 1) * cfg["block_h"]

        q_box_h = 100 if total <= 3 else 82

        q_font, q_lines, q_lh = fit_lines(
            draw,
            f'{idx}) {pergunta["pergunta"]}',
            largura=right - x_question,
            altura=q_box_h,
            max_size=cfg["q_max"],
            min_size=cfg["q_min"],
            max_lines=2,
            bold=True,
        )

        line_boxes = []
        question_strokes = []
        cur_y = top

        for linha in q_lines:
            draw.text(
                (x_question, cur_y),
                linha,
                font=q_font,
                fill=PRETO,
            )

            bb = draw.textbbox((x_question, cur_y), linha, font=q_font)
            line_boxes.append((bb[0], bb[1], bb[2], bb[3]))

            # uma linha de marca-texto por linha da pergunta
            stroke_y = bb[3] + 7
            question_strokes.append((bb[0], stroke_y, bb[2], stroke_y))

            cur_y += q_lh + 5

        question_bottom = max(b[3] for b in line_boxes)

        # Alternativas
        # Há 3 modos compatíveis:
        # 1) "imagem": uma única imagem ao lado das três opções.
        # 2) "imagens_opcoes": uma miniatura ao lado de A, B e C.
        # 3) sem imagem: mantém exatamente o layout antigo.
        imagem_unica_valor = pergunta.get("imagem")
        imagem_unica_path = resolver_imagem_pergunta(imagem_unica_valor) if imagem_unica_valor else None
        tem_imagem_unica = imagem_unica_path is not None

        imagens_valores = pergunta.get("imagens_opcoes", pergunta.get("imagens"))
        tem_imagens_opcoes = (
            not tem_imagem_unica
            and imagens_valores is not None
            and any(v is not None and str(v).strip() for v in imagens_valores)
        )

        if tem_imagem_unica:
            # Imagem maior, horizontal e integrada ao bloco da pergunta.
            # Para 3 perguntas fica mais elegante e legível no celular.
            img_card_w = 330 if total <= 3 else 250
            img_card_h = 170 if total <= 3 else 140
            image_card_x = right - img_card_w
            text_x = x_option
            text_right = image_card_x - 24
            img_size = 0
            imagens_paths = [None, None, None]
        elif tem_imagens_opcoes:
            if total <= 3:
                img_size = 58
            elif total == 4:
                img_size = 42
            else:
                img_size = 30

            image_x = x_option
            text_x = image_x + img_size + 14
            text_right = right
            imagens_paths = [resolver_imagem_opcao(v) for v in imagens_valores]
        else:
            img_size = 0
            image_x = x_option
            text_x = x_option
            text_right = right
            imagens_paths = [None, None, None]

        a_font = fonte(cfg["a_max"], bold=False)

        for size in range(cfg["a_max"], cfg["a_min"] - 1, -2):
            test_font = fonte(size, bold=False)
            ok = True
            for letra, alt in zip(("A", "B", "C"), pergunta["alternativas"]):
                texto = f"{letra}) {alt}"
                bb = draw.textbbox((0, 0), texto, font=test_font)
                if bb[2] - bb[0] > text_right - text_x:
                    ok = False
                    break
            if ok:
                a_font = test_font
                break

        bb_ag = draw.textbbox((0, 0), "Ag", font=a_font)
        a_lh = bb_ag[3] - bb_ag[1]
        option_start_y = question_bottom + 28
        option_boxes = []
        option_strokes = []

        row_content_h = max(a_lh, img_size if tem_imagens_opcoes else 0)
        row_gap = 6 if tem_imagens_opcoes else 8
        row_h = row_content_h + row_gap

        # Desenha uma única imagem ao lado do conjunto A/B/C.
        if tem_imagem_unica:
            card = preparar_imagem_pergunta(
                imagem_unica_path,
                largura=img_card_w,
                altura=img_card_h,
            )
            options_total_h = 3 * row_h - row_gap
            image_card_y = option_start_y + max(0, (options_total_h - img_card_h) // 2)
            img.paste(card, (image_card_x, image_card_y), card)
            draw = ImageDraw.Draw(img)

        for j, (letra, alt) in enumerate(
            zip(("A", "B", "C"), pergunta["alternativas"])
        ):
            oy = option_start_y + j * row_h
            text_y = oy + max(0, (row_content_h - a_lh) // 2)

            circle_x = 105
            circle_y = oy + row_content_h // 2
            r = max(10, int(a_lh * 0.33))

            draw.ellipse(
                [circle_x-r, circle_y-r, circle_x+r, circle_y+r],
                outline=AZUL_ESCURO,
                width=3,
            )

            if tem_imagens_opcoes and imagens_paths[j] is not None:
                thumb = preparar_imagem_opcao(imagens_paths[j], img_size)
                image_y = oy + max(0, (row_content_h - img_size) // 2)
                img.paste(thumb, (image_x, image_y), thumb)
                draw = ImageDraw.Draw(img)

            texto_alt = f"{letra}) {alt}"

            draw.text(
                (text_x, text_y),
                texto_alt,
                font=a_font,
                fill=AZUL_ESCURO,
            )

            bb = draw.textbbox((text_x, text_y), texto_alt, font=a_font)

            box_right = bb[2] + 10
            if tem_imagens_opcoes and imagens_paths[j] is not None:
                box_right = max(box_right, image_x + img_size + 8)

            option_boxes.append((circle_x-r, bb[1]-4, box_right, bb[3]+6))
            option_strokes.append((bb[0], bb[3] + 5, bb[2], bb[3] + 5))

        layouts.append({
            "question_strokes": question_strokes,
            "option_boxes": option_boxes,
            "option_strokes": option_strokes,
            "correcta": int(pergunta["correta"]),
        })

    return img, layouts


# ============================================================
# PINCEL / RISCO
# ============================================================

def aplicar_risco(img, stroke, progresso, cor):
    progresso = max(0.0, min(1.0, float(progresso)))

    x1, y1, x2, _ = stroke
    x_atual = x1 + int((x2 - x1) * progresso)

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # linha grossa, com pontas arredondadas
    draw.line(
        [(x1, y1), (x_atual, y1)],
        fill=cor,
        width=17,
    )

    raio = 8
    draw.ellipse([x1-raio, y1-raio, x1+raio, y1+raio], fill=cor)
    draw.ellipse([x_atual-raio, y1-raio, x_atual+raio, y1+raio], fill=cor)

    return Image.alpha_composite(
        img.convert("RGBA"),
        overlay,
    ).convert("RGB")


def aplicar_risco_multilinha(img, strokes, progresso, cor):
    """Aplica o marca-texto em todas as linhas, na ordem."""
    if not strokes:
        return img

    progresso = max(0.0, min(1.0, float(progresso)))
    n = len(strokes)

    if n == 1:
        return aplicar_risco(img, strokes[0], progresso, cor)

    parte = 1.0 / n
    out = img

    for i, stroke in enumerate(strokes):
        inicio = i * parte
        fim = (i + 1) * parte

        if progresso <= inicio:
            break

        if progresso >= fim:
            p = 1.0
        else:
            p = (progresso - inicio) / parte

        out = aplicar_risco(out, stroke, p, cor)

    return out


def ponta_do_risco(strokes, progresso):
    """Retorna a ponta atual do risco (x, y) respeitando várias linhas."""
    if not strokes:
        return (0, 0)

    progresso = max(0.0, min(1.0, float(progresso)))
    n = len(strokes)

    if n == 1:
        x1, y1, x2, _ = strokes[0]
        return (x1 + int((x2 - x1) * progresso), y1)

    parte = 1.0 / n

    for i, stroke in enumerate(strokes):
        inicio = i * parte
        fim = (i + 1) * parte

        if progresso <= fim or i == n - 1:
            if progresso <= inicio:
                local_p = 0.0
            elif progresso >= fim:
                local_p = 1.0
            else:
                local_p = (progresso - inicio) / parte

            x1, y1, x2, _ = stroke
            return (x1 + int((x2 - x1) * local_p), y1)

    x1, y1, x2, _ = strokes[-1]
    return (x2, y1)


def marcar_resposta(img, option_box, cor):
    # Mantida por compatibilidade, mas não é mais o destaque principal.
    x1, y1, x2, y2 = option_box
    answer_cor = (cor[0], cor[1], cor[2], 55)

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    draw.rounded_rectangle(
        [x1 - 8, y1 - 5, x2 + 12, y2 + 7],
        radius=14,
        fill=answer_cor,
    )

    return Image.alpha_composite(
        img.convert("RGBA"),
        overlay,
    ).convert("RGB")


def colocar_mao(img, strokes, progresso, caminho_mao):
    mao = carregar_mao(caminho_mao)

    tip_x, tip_y = ponta_do_risco(strokes, progresso)

    # A MESMA variável de progresso controla risco e mão:
    # por isso a ponta acompanha o final exato da linha/linhas.
    tip_offset_x = int(mao.width * 0.305)
    tip_offset_y = int(mao.height * 0.015)

    hand_x = tip_x - tip_offset_x
    hand_y = tip_y - tip_offset_y

    canvas = img.convert("RGBA")
    canvas.alpha_composite(mao, (hand_x, hand_y))

    return canvas.convert("RGB")


def render_estado(
    pagina_base,
    layouts,
    atual,
    pincel,
    progresso=1.0,
    mostrar_mao=False,
    mostrar_resposta=False,
    progresso_resposta=1.0,
    mostrar_mao_resposta=False,
):
    img = pagina_base.copy()

    # Perguntas anteriores continuam marcadas em todas as linhas
    for i in range(atual):
        img = aplicar_risco_multilinha(
            img,
            layouts[i]["question_strokes"],
            1.0,
            pincel["cor"],
        )

    # Pergunta atual
    img = aplicar_risco_multilinha(
        img,
        layouts[atual]["question_strokes"],
        progresso,
        pincel["cor"],
    )

    if mostrar_resposta:
        correta = layouts[atual]["correcta"]
        stroke_resposta = [layouts[atual]["option_strokes"][correta]]

        img = aplicar_risco_multilinha(
            img,
            stroke_resposta,
            progresso_resposta,
            pincel["cor"],
        )

        if mostrar_mao_resposta:
            img = colocar_mao(
                img,
                stroke_resposta,
                progresso_resposta,
                pincel["mao"],
            )

    if mostrar_mao:
        img = colocar_mao(
            img,
            layouts[atual]["question_strokes"],
            progresso,
            pincel["mao"],
        )

    return img


# ============================================================
# ÁUDIO
# ============================================================

def limpar_tts(texto):
    return re.sub(r"\s+", " ", str(texto)).strip()


def tts_salvar(texto, caminho):
    caminho = Path(caminho)

    if caminho.exists():
        caminho.unlink()

    executar([
        "edge-tts",
        "--voice", VOZ,
        "--rate", VELOCIDADE_VOZ,
        "--text", limpar_tts(texto),
        "--write-media", str(caminho),
    ])

    if not caminho.exists() or caminho.stat().st_size < 500:
        raise RuntimeError(
            f"Áudio não foi criado: {caminho}"
        )


def duracao_audio(caminho):
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(caminho),
    ]

    return float(
        subprocess.check_output(
            cmd,
            text=True,
        ).strip()
    )


def criar_beep(caminho, frequencia=950):
    executar([
        "ffmpeg",
        "-y",
        "-f", "lavfi",
        "-i", f"sine=frequency={frequencia}:duration=0.14",
        "-af", "volume=0.5,apad=pad_dur=1",
        "-t", "1.0",
        "-c:a", "aac",
        "-b:a", "160k",
        "-ar", str(AUDIO_HZ),
        "-ac", str(AUDIO_CHANNELS),
        str(caminho),
    ])


# ============================================================
# VÍDEO
# ============================================================

def criar_clipe_imagem(img_path, duracao, saida, audio=None):
    duracao = float(duracao)

    if audio:
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(img_path),
            "-i", str(audio),
            "-t", f"{duracao:.3f}",
            "-vf", f"scale={W}:{H},fps={FPS},format=yuv420p",
            "-af", f"aresample={AUDIO_HZ}:async=1:first_pts=0,apad",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "20",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "160k",
            "-ar", str(AUDIO_HZ),
            "-ac", str(AUDIO_CHANNELS),
            "-shortest",
            "-movflags", "+faststart",
            str(saida),
        ]
    else:
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(img_path),
            "-f", "lavfi",
            "-i", f"anullsrc=channel_layout=stereo:sample_rate={AUDIO_HZ}",
            "-t", f"{duracao:.3f}",
            "-vf", f"scale={W}:{H},fps={FPS},format=yuv420p",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "20",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "160k",
            "-ar", str(AUDIO_HZ),
            "-ac", str(AUDIO_CHANNELS),
            "-shortest",
            "-movflags", "+faststart",
            str(saida),
        ]

    executar(cmd)


def criar_clipe_animado(frame_dir, duracao, audio, saida):
    executar([
        "ffmpeg", "-y",
        "-framerate", str(ANIM_FPS),
        "-i", str(frame_dir / "frame_%04d.jpg"),
        "-i", str(audio),
        "-t", f"{duracao:.3f}",
        "-vf", f"scale={W}:{H},fps={FPS},format=yuv420p",
        "-af", f"aresample={AUDIO_HZ}:async=1:first_pts=0,apad",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "160k",
        "-ar", str(AUDIO_HZ),
        "-ac", str(AUDIO_CHANNELS),
        "-shortest",
        "-movflags", "+faststart",
        str(saida),
    ])


def concatenar_clipes(clipes, saida, lista_path):
    lista_path.write_text(
        "\n".join(
            f"file '{Path(c).resolve().as_posix()}'"
            for c in clipes
        ),
        encoding="utf-8",
    )

    executar([
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(lista_path),
        "-c", "copy",
        "-movflags", "+faststart",
        str(saida),
    ])


# ============================================================
# GERAÇÃO
# ============================================================

def gerar_video_tema(tema, perguntas, indice, total_temas):
    validar_tema(tema, perguntas)

    pincel = pincel_do_video(indice)

    print(
        f"\n🎬 {indice:02d}/{total_temas:02d} — {tema} "
        f"| pincel: {pincel['nome']}"
    )

    pagina_base, layouts = criar_pagina_base(
        tema,
        perguntas,
    )

    pasta_tema = PASTA_TMP / slug(tema)
    pasta_tema.mkdir(parents=True, exist_ok=True)

    clipes = []

    beep = pasta_tema / "beep.m4a"
    criar_beep(beep)

    for q_idx, pergunta in enumerate(perguntas):
        numero = q_idx + 1
        base_num = numero * 10

        # 1. Pergunta + mão passando
        audio_pergunta = pasta_tema / f"{numero:02d}_pergunta.mp3"

        # LÊ SOMENTE A PERGUNTA
        tts_salvar(
            pergunta["pergunta"],
            audio_pergunta,
        )

        dur = duracao_audio(audio_pergunta) + PAUSA_DEPOIS_PERGUNTA

        frame_dir = pasta_tema / f"frames_{numero:02d}"

        if frame_dir.exists():
            shutil.rmtree(frame_dir)

        frame_dir.mkdir(parents=True, exist_ok=True)

        total_frames = max(
            12,
            int(math.ceil(dur * ANIM_FPS)),
        )

        for f in range(total_frames):
            progresso = f / max(1, total_frames - 1)

            frame = render_estado(
                pagina_base,
                layouts,
                q_idx,
                pincel,
                progresso=progresso,
                mostrar_mao=True,
                mostrar_resposta=False,
            )

            frame.save(
                frame_dir / f"frame_{f:04d}.jpg",
                quality=91,
            )

        clip_pergunta = pasta_tema / f"{base_num:03d}_pergunta.mp4"

        criar_clipe_animado(
            frame_dir,
            dur,
            audio_pergunta,
            clip_pergunta,
        )

        clipes.append(clip_pergunta)

        # 2. Contagem 3, 2, 1
        for n in (3, 2, 1):
            count_img = render_estado(
                pagina_base,
                layouts,
                q_idx,
                pincel,
                progresso=1.0,
                mostrar_mao=False,
                mostrar_resposta=False,
            )

            draw = ImageDraw.Draw(count_img)

            cx, cy, r = 940, 455, 48

            draw.ellipse(
                [cx-r, cy-r, cx+r, cy+r],
                fill=AZUL,
            )

            txt = str(n)
            fnt = fonte(43, bold=True)
            bb = draw.textbbox((0, 0), txt, font=fnt)

            draw.text(
                (
                    cx - (bb[2]-bb[0])/2,
                    cy - (bb[3]-bb[1])/2 - 3,
                ),
                txt,
                font=fnt,
                fill=BRANCO,
            )

            count_png = pasta_tema / f"{numero:02d}_count_{n}.png"
            count_img.save(count_png)

            count_clip = pasta_tema / f"{base_num + (4-n):03d}_count_{n}.mp4"

            criar_clipe_imagem(
                count_png,
                1.0,
                count_clip,
                beep,
            )

            clipes.append(count_clip)

        # 3. Resposta correta com marca-texto e mão
        correta = int(pergunta["correta"])
        resposta = pergunta["alternativas"][correta]

        audio_resposta = pasta_tema / f"{numero:02d}_resposta.mp3"

        # LÊ SOMENTE A RESPOSTA CORRETA
        tts_salvar(
            f"A resposta correta é: {resposta}.",
            audio_resposta,
        )

        answer_dur = duracao_audio(audio_resposta) + PAUSA_DEPOIS_RESPOSTA

        answer_frames = pasta_tema / f"frames_resposta_{numero:02d}"
        if answer_frames.exists():
            shutil.rmtree(answer_frames)
        answer_frames.mkdir(parents=True, exist_ok=True)

        total_answer_frames = max(
            12,
            int(math.ceil(answer_dur * ANIM_FPS)),
        )

        for f in range(total_answer_frames):
            progresso_resposta = f / max(1, total_answer_frames - 1)

            answer_img = render_estado(
                pagina_base,
                layouts,
                q_idx,
                pincel,
                progresso=1.0,
                mostrar_mao=False,
                mostrar_resposta=True,
                progresso_resposta=progresso_resposta,
                mostrar_mao_resposta=True,
            )

            answer_img.save(
                answer_frames / f"frame_{f:04d}.jpg",
                quality=91,
            )

        answer_clip = pasta_tema / f"{base_num + 4:03d}_resposta.mp4"

        criar_clipe_animado(
            answer_frames,
            answer_dur,
            audio_resposta,
            answer_clip,
        )

        clipes.append(answer_clip)

    # Tela final
    final_img = pagina_base.copy()

    for layout in layouts:
        final_img = aplicar_risco_multilinha(
            final_img,
            layout["question_strokes"],
            1.0,
            pincel["cor"],
        )

    draw = ImageDraw.Draw(final_img)
    final_text = "QUANTAS VOCÊ ACERTOU?"
    fnt = fonte(35, bold=True)
    bb = draw.textbbox((0, 0), final_text, font=fnt)

    tx = (W - (bb[2]-bb[0])) / 2
    ty = 1765

    draw.rounded_rectangle(
        [tx-25, ty-12, tx+(bb[2]-bb[0])+25, ty+52],
        radius=25,
        fill=BRANCO,
    )

    draw.text(
        (tx, ty),
        final_text,
        font=fnt,
        fill=AZUL_ESCURO,
    )

    final_png = pasta_tema / "final.png"
    final_img.save(final_png)

    final_audio = pasta_tema / "final.mp3"

    tts_salvar(
        "Quantas você acertou?",
        final_audio,
    )

    final_dur = duracao_audio(final_audio) + 0.7
    final_clip = pasta_tema / "999_final.mp4"

    criar_clipe_imagem(
        final_png,
        final_dur,
        final_clip,
        final_audio,
    )

    clipes.append(final_clip)

    PASTA_SAIDA.mkdir(parents=True, exist_ok=True)

    saida = PASTA_SAIDA / f"{indice:02d}_{slug(tema)}_{pincel['nome']}.mp4"

    concatenar_clipes(
        clipes,
        saida,
        pasta_tema / "concat.txt",
    )

    print(f"✅ {saida}")
    return saida


# ============================================================
# PREVIEW
# ============================================================

def preview():
    if not QUIZZES:
        raise ValueError("QUIZZES está vazio.")

    tema, perguntas = next(iter(QUIZZES.items()))
    validar_tema(tema, perguntas)

    pagina, layouts = criar_pagina_base(
        tema,
        perguntas,
    )

    # cria um preview para cada uma das 5 cores
    for indice, pincel in enumerate(PINCEIS, start=1):
        prev = render_estado(
            pagina,
            layouts,
            atual=0,
            pincel=pincel,
            progresso=0.70,
            mostrar_mao=True,
            mostrar_resposta=False,
        )

        prev.save(
            f"preview_{indice}_{pincel['nome']}.png"
        )

    print("✅ 5 previews criados.")


# ============================================================
# MAIN
# ============================================================

def main():
    if "--preview" in sys.argv:
        preview()
        return

    if not QUIZZES:
        raise ValueError("QUIZZES está vazio.")

    if PASTA_TMP.exists():
        shutil.rmtree(PASTA_TMP)

    PASTA_TMP.mkdir(parents=True, exist_ok=True)
    PASTA_SAIDA.mkdir(parents=True, exist_ok=True)

    temas = list(QUIZZES.items())
    gerados = []

    for indice, (tema, perguntas) in enumerate(
        temas,
        start=1,
    ):
        video = gerar_video_tema(
            tema,
            perguntas,
            indice,
            len(temas),
        )
        gerados.append(video)

    print(
        f"\n✅ Finalizado. "
        f"{len(gerados)} vídeo(s) gerado(s)."
    )

    for video in gerados:
        print(" -", video)


if __name__ == "__main__":
    main()
