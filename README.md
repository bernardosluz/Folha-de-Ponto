# 📄 Gerador Automático de Folha de Ponto - Governo de Sergipe

Automação em Python projetada para gerar e compilar folhas de frequência de estágio em formato PDF utilizando LaTeX. O script calcula automaticamente dias úteis, fins de semana, pontos facultativos e feriados (nacionais e do estado de Sergipe), preenchendo os horários de entrada e saída.

---

## 🛠️ Tecnologias e Dependências

Este projeto não requer a instalação de pacotes externos do Python via `pip`, pois utiliza apenas bibliotecas nativas. No entanto, ele depende de um compilador LaTeX no sistema operacional.

1. **Python 3.x**: Para executar a lógica de automação e cálculo de datas
   * **Windowns:** Necessário instalar o [Python](https://www.python.org/downloads/).
2. **Distribuição LaTeX**: Necessária para interpretar o arquivo `.tex` e gerar o `.pdf`.
   * **Windows:** Recomendado instalar o [MiKTeX](https://miktex.org/download).
   * **Linux:** `sudo apt install texlive-latex-base texlive-fonts-recommended texlive-lang-portuguese`
*Nota: Certifique-se de que o comando `pdflatex` e `python` estão adicionados ao `PATH` das Variáveis de Ambiente do seu sistema após as instalações.*

---

## ⚙️ Configuração Inicial

Antes de rodar o script pela primeira vez, duas configurações são necessárias:

### 1. Dados do Estagiário
Abra o arquivo `gerar_folha_latex.py` e edite o dicionário `DADOS` (localizado no início do código) com as suas informações pessoais, horários e dados do supervisor:

```python
DADOS = {
    "nome": "Seu Nome Completo",
    "local": "Secretaria de Estado da Segurança Pública",
    "curso": "",
    "instituicao": "",
    "telefone": "(XX) XXXXX-XXXX",
    "horario_inicio": "",     
    "horario_termino": "",  
    "responsavel_nome": "Nome do Supervisor",
    "responsavel_instituicao": r"",
}