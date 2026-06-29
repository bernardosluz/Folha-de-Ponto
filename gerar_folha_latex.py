#!/usr/bin/env python3
# =============================================================================
# GERADOR AUTOMÁTICO DE FOLHA DE PONTO - GOVERNO DE SERGIPE
# =============================================================================
# Este script gera a folha de frequência de estagiário em LaTeX/PDF
# automaticamente para QUALQUER mês/ano, calculando:
#   - Fins de semana (sábado/domingo)
#   - Feriados nacionais fixos (ex: 07/09, 15/11, 25/12)
#   - Feriados nacionais móveis (Carnaval, Sexta-feira Santa, Corpus Christi)
#   - Feriados estaduais de Sergipe (08/07 - Emancipação)
#   - Pontos facultativos comuns (pós-Carnaval, Corpus Christi, etc.)
#
# USO:
#   python gerar_folha.py                  → gera para o mês ATUAL
#   python gerar_folha.py 12 2025          → gera para dezembro/2025
#   python gerar_folha.py 3 2026           → gera para março/2026
#
# COMO FUNCIONA:
#   1. Calcula a Páscoa (algoritmo de Gauss) → base para feriados móveis
#   2. Monta lista de feriados e pontos facultativos do mês
#   3. Gera código LaTeX com a tabela preenchida
#   4. Compila com pdflatex → PDF pronto
# =============================================================================

import calendar
import subprocess
import sys
import os
from datetime import date, timedelta


# =============================================================================
# DADOS DO ESTAGIÁRIO (edite aqui para personalizar)
# =============================================================================
DADOS = {
    "nome": "Seu Nome Completo",
    "local": "Secretaria de Estado da Segurança Pública",
    "curso": "Seu Curso de Graduação",
    "instituicao": "Sua Instituição de Ensino",
    "telefone": "(XX) XXXXX-XXXX",
    "horario_inicio": "XX-XX",  # horário padrão de entrada
    "horario_termino": "XX-XX",  # horário padrão de saída
    # Dados do responsável técnico
    "responsavel_nome": "Nome do Supervisor",
    "responsavel_instituicao": r"",
}

# =============================================================================
# CÁLCULO DA PÁSCOA - Algoritmo de Butcher (Gauss)
# =============================================================================
# A Páscoa é a base de TODOS os feriados móveis no Brasil.
# O algoritmo calcula a data da Páscoa para qualquer ano.
#
# Por que isso importa?
#   Carnaval       = Páscoa - 47 dias
#   Sexta-Santa    = Páscoa - 2 dias
#   Corpus Christi = Páscoa + 60 dias
#
# O algoritmo usa divisões modulares (resto de divisão) para encontrar
# o ciclo lunar que determina a Páscoa no calendário gregoriano.

def calcular_pascoa(ano: int) -> date:
    """
    Calcula a data da Páscoa para um dado ano.
    
    Retorna: objeto date com a data da Páscoa.
    
    Baseado no algoritmo de Butcher (1876), que é uma versão
    simplificada do cálculo eclesiástico da Páscoa.
    Cada variável intermediária (a, b, c...) representa um passo
    do ciclo metônico (relação entre anos solares e lunares).
    """
    a = ano % 19          # Posição no ciclo metônico (19 anos)
    b = ano // 100        # Século
    c = ano % 100         # Ano dentro do século
    d = b // 4            # Correção de anos bissextos seculares
    e = b % 4             # Resto da correção
    f = (b + 8) // 25     # Correção de sincronização
    g = (b - f + 1) // 3  # Mais ajustes
    h = (19 * a + b - d - g + 15) % 30  # Epacta (idade da lua)
    i = c // 4            # Bissexto dentro do século
    k = c % 4             # Resto
    l = (32 + 2 * e + 2 * i - h - k) % 7  # Dia da semana
    m = (a + 11 * h + 22 * l) // 451       # Correção final
    mes = (h + l - 7 * m + 114) // 31      # Mês (3=março, 4=abril)
    dia = ((h + l - 7 * m + 114) % 31) + 1  # Dia do mês
    return date(ano, mes, dia)


# =============================================================================
# MONTAGEM DA LISTA DE FERIADOS E PONTOS FACULTATIVOS
# =============================================================================

def obter_feriados(ano: int) -> dict[date, str]:
    """
    Retorna um dicionário {data: "nome do feriado"} com todos os
    feriados NACIONAIS (fixos e móveis) e ESTADUAIS de Sergipe.
    
    Feriados fixos: sempre caem na mesma data todo ano.
    Feriados móveis: dependem da Páscoa (que muda todo ano).
    """
    pascoa = calcular_pascoa(ano)
    
    feriados = {
        # --- FERIADOS NACIONAIS FIXOS ---
        # Lei nº 662/1949 e Lei nº 6.802/1980
        date(ano, 1, 1):   "Confraternização Universal",
        date(ano, 4, 21):  "Tiradentes",
        date(ano, 5, 1):   "Dia do Trabalho",
        date(ano, 9, 7):   "Independência do Brasil",
        date(ano, 10, 12): "N. Sra. Aparecida",
        date(ano, 11, 2):  "Finados",
        date(ano, 11, 15): "Proclamação da República",
        date(ano, 11, 20): "Consciência Negra",  # Lei nº 14.759/2023
        date(ano, 12, 25): "Natal",
        
        # --- FERIADOS NACIONAIS MÓVEIS ---
        # Calculados a partir da Páscoa
        # timedelta(days=N) cria um intervalo de N dias que somamos/subtraímos
        (pascoa - timedelta(days=47)): "Carnaval (2ª-feira)",   # Seg de Carnaval
        (pascoa - timedelta(days=46)): "Carnaval (3ª-feira)",   # Ter de Carnaval
        (pascoa - timedelta(days=2)):  "Sexta-feira Santa",
        (pascoa):                       "Páscoa",
        (pascoa + timedelta(days=60)): "Corpus Christi",
        
        # --- FERIADO ESTADUAL DE SERGIPE ---
        # Lei Estadual - Emancipação Política de Sergipe
        date(ano, 7, 8):   "Emancipação de Sergipe",
    }
    
    return feriados


def obter_pontos_facultativos(ano: int) -> dict[date, str]:
    """
    Retorna dicionário {data: "descrição"} com os pontos facultativos
    mais comuns. Estes NÃO são feriados oficiais, mas geralmente são
    decretados pelo governo estadual/federal.
    
    ATENÇÃO: Pontos facultativos variam por decreto a cada ano.
    Esta lista cobre os mais recorrentes, mas pode precisar de ajuste.
    Verifique o decreto estadual de Sergipe para o ano específico.
    """
    pascoa = calcular_pascoa(ano)
    
    facultativos = {
        # Quarta-feira de Cinzas (dia seguinte ao Carnaval, geralmente meio expediente)
        (pascoa - timedelta(days=45)): "Ponto Facultativo (Cinzas)",
        
        # Dia após Corpus Christi (sexta-feira, fazendo "ponte")
        (pascoa + timedelta(days=61)): "Ponto Facultativo",
        
        # Véspera de Natal (24/12) - comum em muitos estados
        date(ano, 12, 24): "Ponto Facultativo (Véspera Natal)",
        
        # Véspera de Ano Novo (31/12)
        date(ano, 12, 31): "Ponto Facultativo (Véspera Ano Novo)",
        
        # Dia do Servidor Público (28/10) - facultativo federal
        date(ano, 10, 28): "Ponto Facultativo (Servidor Público)",
    }
    
    return facultativos


# =============================================================================
# CLASSIFICAÇÃO DE CADA DIA DO MÊS
# =============================================================================

def classificar_dias(ano: int, mes: int) -> list[dict]:
    """
    Para cada dia do mês, determina se é:
      - "util"        → dia normal de trabalho
      - "sabado"      → sábado (sem expediente)
      - "domingo"     → domingo (sem expediente)
      - "feriado"     → feriado oficial
      - "facultativo" → ponto facultativo
    
    Retorna lista de dicionários, um por dia, com:
      - "dia": int (1-31)
      - "data": objeto date
      - "tipo": string com a classificação
      - "descricao": nome do feriado/facultativo (ou vazio)
    
    calendar.monthrange(ano, mes) retorna uma tupla:
      (dia_da_semana_do_1º_dia, total_de_dias_no_mês)
      Ex: (1, 30) → o mês começa na terça e tem 30 dias
    """
    feriados = obter_feriados(ano)
    facultativos = obter_pontos_facultativos(ano)
    
    # monthrange retorna (weekday_do_dia_1, num_dias_no_mes)
    # weekday: 0=segunda, 1=terça, ..., 5=sábado, 6=domingo
    _, num_dias = calendar.monthrange(ano, mes)
    
    dias = []
    for dia in range(1, num_dias + 1):
        d = date(ano, mes, dia)
        
        # .weekday() retorna 0=seg, 1=ter, ..., 5=sáb, 6=dom
        dia_semana = d.weekday()
        
        # Verificação em ordem de prioridade:
        # 1º feriados, 2º facultativos, 3º fim de semana, 4º dia útil
        if d in feriados:
            tipo = "feriado"
            descricao = feriados[d]
        elif d in facultativos:
            tipo = "facultativo"
            descricao = facultativos[d]
        elif dia_semana == 5:  # 5 = sábado
            tipo = "sabado"
            descricao = ""
        elif dia_semana == 6:  # 6 = domingo
            tipo = "domingo"
            descricao = ""
        else:
            tipo = "util"
            descricao = ""
        
        dias.append({
            "dia": dia,
            "data": d,
            "tipo": tipo,
            "descricao": descricao,
        })
    
    return dias


# =============================================================================
# GERAÇÃO DO CÓDIGO LATEX
# =============================================================================

# Nomes dos meses em português (índice 0 vazio para alinhar com 1-12)
MESES_PT = [
    "", "JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO",
    "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"
]


def gerar_linha_tabela(dia_info: dict, ano: int, mes: int) -> str:
    """
    Gera uma linha da tabela LaTeX para um dia específico.
    
    Lógica:
      - Dia útil (seg/qua/sex): data & 8:00 & 12:00 & (em branco)
      - Dia útil (ter/qui):     data & DECLARAÇÃO & DECLARAÇÃO & DECLARAÇÃO
      - Sábado/Domingo:         data & SÁBADO/DOMINGO & mesmo & XXXXX (cinza)
      - Feriado:                data & XXXXXXXXX & XXXXXXXXX & FERIADO
      - Facultativo:            data & XXXXXXXXX & XXXXXXXXX & Ponto Facultativo
    
    f-string: f"..." permite inserir variáveis Python direto no texto
    com {variavel}. É o jeito moderno de formatar strings em Python.
    """
    # Formata a data como DD/MM/AAAA
    data_str = f"{dia_info['dia']:02d}/{mes:02d}/{ano}"
    
    # Monta a linha conforme o tipo do dia
    if dia_info["tipo"] == "sabado":
        linha = f"{data_str} & SÁBADO & SÁBADO & \\semexpediente"
    
    elif dia_info["tipo"] == "domingo":
        linha = f"{data_str} & DOMINGO & DOMINGO & \\semexpediente"
    
    elif dia_info["tipo"] == "feriado":
        # Mostra o nome do feriado na coluna de assinatura
        nome = dia_info["descricao"]
        linha = f"{data_str} & XXXXXXXXX & XXXXXXXXX & FERIADO"
    
    elif dia_info["tipo"] == "facultativo":
        descricao = dia_info["descricao"]
        linha = f"{data_str} & XXXXXXXXX & XXXXXXXXX & {{descricao}}"
    
    else:  # dia útil
        # .weekday() → 0=seg, 1=ter, 2=qua, 3=qui, 4=sex
        # Todos os dias úteis normais: horário preenchido, assinatura em branco
        h_ini = DADOS["horario_inicio"]
        h_fim = DADOS["horario_termino"]
        linha = f"{data_str} & {h_ini} & {h_fim} &"
    
    # Adiciona o \\ (quebra de linha LaTeX) e \hline (linha horizontal)
    return f"{linha} \\\\ \\hline"


def gerar_latex(ano: int, mes: int) -> str:
    """
    Monta o documento LaTeX completo como uma string.
    
    Usa uma "template string" (texto longo entre aspas triplas)
    onde inserimos as variáveis com f-string.
    
    O 'r' antes das aspas (raw string) evita que o Python interprete
    as barras invertidas (\\) — essencial porque LaTeX usa \\ pra tudo.
    """
    # Classifica todos os dias do mês
    dias = classificar_dias(ano, mes)
    
    # Gera todas as linhas da tabela
    linhas_tabela = "\n".join(
        gerar_linha_tabela(d, ano, mes) for d in dias
    )
    
    # Nome do mês em português
    nome_mes = MESES_PT[mes]
    
    # --- TEMPLATE DO DOCUMENTO LATEX ---
    # Cada seção está explicada nos comentários dentro do próprio LaTeX
    latex = rf"""% ===========================================================================
% FOLHA DE PONTO GERADA AUTOMATICAMENTE
% Mês: {nome_mes}/{ano}
% Gerado por: gerar_folha_latex.py
% ===========================================================================

\documentclass[a4paper, 11pt]{{article}}

% --- PACOTES ---
\usepackage[utf8]{{inputenc}}      % Suporte a acentos (UTF-8)
\usepackage[T1]{{fontenc}}         % Codificação de fontes para PT-BR
\usepackage[top=1.2cm, bottom=1.5cm, left=2cm, right=2cm]{{geometry}}  % Margens
\usepackage{{array}}               % Formatação avançada de tabelas
\usepackage{{makecell}}            % Quebra de linha em células
\usepackage{{xcolor}}              % Cores (para os XXXX cinza)
\usepackage{{graphicx}}
\usepackage{{grffile}}

% --- CONFIGURAÇÕES ---
\pagestyle{{empty}}                % Sem número de página
\setlength{{\parindent}}{{0pt}}    % Sem recuo de parágrafo
\setlength{{\parskip}}{{3pt}}      % Espaço entre parágrafos

% --- COMANDOS PERSONALIZADOS ---
\newcommand{{\semexpediente}}{{\textcolor{{gray}}{{**********************************}}}}
\newcommand{{\assinatura}}{{\textit{{{DADOS['nome']}}}}}

\begin{{document}}

% === CABEÇALHO INSTITUCIONAL ===
\begin{{center}}
    \begin{{figure}}[h]
        \centering
        \includegraphics[width=0.15\textwidth]{{logo_ssp_pb.png}}
    \end{{figure}}
    {{\Large \textbf{{GOVERNO DE SERGIPE}}}}\\[1pt]
    {{\large \textbf{{\textit{{SECRETARIA DE ESTADO DA SEGURANÇA PÚBLICA}}}}}}\\[1pt]
    {{\large \textbf{{\textit{{SETOR DE ESTÁGIO}}}}}}\\[0.25cm]
\end{{center}}

% === DADOS DO ESTAGIÁRIO ===
\textbf{{Nome: {DADOS['nome']}}}\\[1pt]
\textbf{{Local de Trabalho: {DADOS['local']}}}\\[1pt]
\textbf{{Curso: {DADOS['curso']}}}\\[1pt]
\textbf{{Instituição de Ensino: {DADOS['instituicao']}}}\\[1pt]
\textbf{{Telefone para Contato:}} {DADOS['telefone']}\\[0.3cm]

% === TÍTULO ===
\begin{{center}}
    {{\large \textbf{{FREQUÊNCIA ESTAGIÁRIO -- {nome_mes} {ano}}}}}\\[0.2cm]
\end{{center}}

% === TABELA DE FREQUÊNCIA ===
\renewcommand{{\arraystretch}}{{1.05}}
\begin{{center}}
\small
\begin{{tabular}}{{|>{{\centering\arraybackslash}}p{{2.5cm}}
                |>{{\centering\arraybackslash}}p{{2.5cm}}
                |>{{\centering\arraybackslash}}p{{2.5cm}}
                |>{{\centering\arraybackslash}}p{{6.5cm}}|}}
\hline
\textbf{{DATA}} &
\makecell{{\textbf{{HORÁRIO}} \\ \textbf{{INÍCIO}}}} &
\makecell{{\textbf{{HORÁRIO}} \\ \textbf{{TÉRMINO}}}} &
\makecell{{\textbf{{ASSINATURA}} \\ \textbf{{ESTAGIÁRIO}}}} \\
\hline
{linhas_tabela}
\end{{tabular}}
\end{{center}}

% === RODAPÉ COM ASSINATURA ===
\vfill
\begin{{center}}
    \textbf{{{DADOS['responsavel_nome']}}}\\[1pt]
    \rule{{8cm}}{{0.4pt}}\\[2pt]
    Assinatura do Responsável Técnico
\end{{center}}

\end{{document}}
"""
    return latex


# =============================================================================
# COMPILAÇÃO: LATEX → PDF
# =============================================================================

def compilar_pdf(tex_path: str, pasta_saida: str) -> bool:
    """
    Compila o arquivo .tex em .pdf usando pdflatex e salva na pasta especificada.
    Trata exceções caso o compilador não esteja instalado no sistema.
    """
    os.makedirs(pasta_saida, exist_ok=True)
    
    try:
        resultado = subprocess.run(
            [
                "pdflatex",
                "-interaction=nonstopmode",
                f"-output-directory={pasta_saida}",
                tex_path
            ],
            capture_output=True,
            text=False
        )
        
        if resultado.returncode == 0:
            return True
        else:
            print("  [X] ERRO na compilação LaTeX:")
            saida = resultado.stdout.decode("utf-8", errors="replace")
            print(saida[-500:])
            return False
            
    except FileNotFoundError:
        # Captura especificamente o erro do Windows de não achar o 'pdflatex'
        print("\n  [X] ERRO CRÍTICO: Compilador LaTeX não encontrado!")
        print("  O comando 'pdflatex' não está disponível no PATH do Windows.")
        print("  -> Solução: Instale o MiKTeX (ou TeX Live) e reinicie o terminal.")
        return False


# =============================================================================
# RELATÓRIO: mostra quais feriados foram detectados
# =============================================================================

def imprimir_resumo(ano: int, mes: int):
    """
    Imprime no terminal um resumo dos dias especiais encontrados.
    Útil para conferir se os feriados estão corretos.
    """
    dias = classificar_dias(ano, mes)
    
    print(f"\n{'='*55}")
    print(f"  FOLHA DE PONTO — {MESES_PT[mes]} {ano}")
    print(f"{'='*55}")
    
    # Contadores
    # Dias úteis presenciais: úteis que NÃO são terça(1) nem quinta(3)
    # Dias de declaração: terças e quintas que são dias úteis
    uteis_todos = [d for d in dias if d["tipo"] == "util"]
    presenciais = len(uteis_todos)
    feriados = [d for d in dias if d["tipo"] == "feriado"]
    facultativos = [d for d in dias if d["tipo"] == "facultativo"]
    sabados = sum(1 for d in dias if d["tipo"] == "sabado")
    domingos = sum(1 for d in dias if d["tipo"] == "domingo")
    
    print(f"\n  Dias presenciais:    {presenciais}")
    print(f"  Sábados:             {sabados}")
    print(f"  Domingos:            {domingos}")
    
    if feriados:
        print(f"\n  FERIADOS ({len(feriados)}):")
        for f in feriados:
            print(f"    {f['data'].strftime('%d/%m')} — {f['descricao']}")
    
    if facultativos:
        print(f"\n  PONTOS FACULTATIVOS ({len(facultativos)}):")
        for f in facultativos:
            print(f"    {f['data'].strftime('%d/%m')} — {f['descricao']}")
    
    print(f"\n{'='*55}\n")


# =============================================================================
# EXECUÇÃO PRINCIPAL
# =============================================================================
# sys.argv é uma lista com os argumentos passados na linha de comando.
#   sys.argv[0] = nome do script ("gerar_folha.py")
#   sys.argv[1] = primeiro argumento (mês)
#   sys.argv[2] = segundo argumento (ano)
#
# Se nenhum argumento for passado, usa o mês e ano atuais.

if __name__ == "__main__":
    # Decide mês e ano: via argumento ou mês atual
    if len(sys.argv) >= 3:
        mes = int(sys.argv[1])
        ano = int(sys.argv[2])
    elif len(sys.argv) == 2:
        mes = int(sys.argv[1])
        ano = date.today().year
    else:
        hoje = date.today()
        mes = hoje.month
        ano = hoje.year
    
    # Validação básica
    if not (1 <= mes <= 12):
        print(f"Erro: mês inválido ({mes}). Use um valor entre 1 e 12.")
        sys.exit(1)
    
    # Mostra resumo no terminal
    imprimir_resumo(ano, mes)
    
    # Gera o código LaTeX
    codigo_latex = gerar_latex(ano, mes)
    
    # Nome do arquivo baseado no mês/ano
    nome_base = f"folha_ponto_{MESES_PT[mes].lower()}_{ano}"
    
    # Define os nomes das pastas
    pasta_tex = "Code_Tex"
    pasta_pdf = "Pdf_Tex"
    
    # Cria as pastas caso elas não existam no diretório
    os.makedirs(pasta_tex, exist_ok=True)
    
    # Define os caminhos completos
    tex_path = os.path.join(pasta_tex, f"{nome_base}.tex")
    pdf_path = os.path.join(pasta_pdf, f"{nome_base}.pdf")
    
    # Salva o arquivo .tex dentro da pasta Code_Tex
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(codigo_latex)
    print(f"  Arquivo .tex salvo em: {tex_path}")
    
    # Compila para PDF direcionando a saída para a pasta Pdf_Tex
    print(f"  Compilando PDF...")
    if compilar_pdf(tex_path, pasta_pdf):
        print(f"  PDF gerado com sucesso em: {pdf_path}")
    else:
        print(f"  Falha ao gerar PDF. Verifique o log.")
        sys.exit(1)