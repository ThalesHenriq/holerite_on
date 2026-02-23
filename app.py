import streamlit as st
from fpdf import FPDF
import io

# Função INSS 2026 (progressiva real)
def calcular_inss(base):
    faixas = [
        (1621.00, 0.075, 0),
        (2902.84, 0.09, 1621.00 * 0.075),
        (4354.27, 0.12, 1621.00 * 0.075 + (2902.84 - 1621.00) * 0.09),
        (8475.55, 0.14, 1621.00 * 0.075 + (2902.84 - 1621.00) * 0.09 + (4354.27 - 2902.84) * 0.12)
    ]
    inss = 0
    prev = 0
    for teto, aliquota, ded_ant in faixas:
        if base <= prev:
            break
        faixa = min(base, teto) - prev
        inss += faixa * aliquota
        prev = teto
    if base > 8475.55:
        inss = 8475.55 * 0.14  # teto aproximado (ajuste se houver atualização)
    return round(inss, 2)

# Função IRRF 2026 (tabela progressiva mensal, sem dependentes)
def calcular_irrf(base_ir):
    faixas = [
        (2428.80, 0.00, 0.00),
        (2826.65, 0.075, 182.16),
        (3751.05, 0.15, 394.16),
        (4664.68, 0.225, 675.49),
        (float('inf'), 0.275, 908.73)
    ]
    for limite, aliquota, deducao in faixas:
        if base_ir <= limite:
            irrf = (base_ir * aliquota) - deducao
            return max(round(irrf, 2), 0.00)
    return 0.00  # fallback

# Interface
st.title("Gerador de Holerite 2026 - Ajuda ao RH")

tab1, tab2 = st.tabs(["Dados Fixos", "Cálculo Salarial"])

with tab1:
    st.header("Dados da Empresa e Funcionário")
    col1, col2 = st.columns(2)
    with col1:
        nome_empresa = st.text_input("Nome da Empresa", "Minha Empresa Ltda")
        cnpj = st.text_input("CNPJ", "00.000.000/0000-00")
        endereco = st.text_input("Endereço", "Rua Exemplo, 123 - Franca/SP")
    with col2:
        nome_func = st.text_input("Nome do Funcionário", "Pugvelop Silva")
        cpf = st.text_input("CPF", "000.000.000-00")
        cargo = st.text_input("Cargo", "Desenvolvedor")
        data_adm = st.text_input("Admissão (DD/MM/AAAA)", "01/01/2023")
        mes_ano = st.text_input("Competência", "Fevereiro/2026")

with tab2:
    st.header("Salário Base e Itens Variáveis")
    salario_base = st.number_input("Salário Base (R$)", min_value=0.0, value=3000.0, step=100.0)

    st.subheader("Adicionar Itens (Proventos ou Descontos)")
    
    # Lista de itens (usamos session_state para persistir)
    if 'itens' not in st.session_state:
        st.session_state.itens = []

    desc = st.text_input("Descrição do item", "")
    valor_item = st.number_input("Valor (R$)", min_value=-99999.0, value=0.0, step=10.0)
    tipo_item = st.radio("Tipo", ["Provento (+)", "Desconto (-)"], horizontal=True)

    if st.button("Adicionar Item"):
        if desc.strip():
            st.session_state.itens.append({
                "descricao": desc,
                "valor": valor_item if tipo_item == "Provento (+)" else -abs(valor_item),
                "tipo": tipo_item
            })
            st.success(f"Item '{desc}' adicionado!")
        else:
            st.warning("Digite uma descrição.")

    # Exibir itens adicionados
    if st.session_state.itens:
        st.subheader("Itens Adicionados")
        total_proventos_var = 0
        total_descontos_var = 0
        
        for i, item in enumerate(st.session_state.itens):
            col1, col2, col3 = st.columns([4, 2, 1])
            col1.write(item["descricao"])
            sinal = "+" if item["valor"] >= 0 else "-"
            col2.write(f"R$ {abs(item['valor']):.2f} {sinal}")
            if col3.button("Remover", key=f"rem_{i}"):
                del st.session_state.itens[i]
                st.rerun()

            if item["valor"] >= 0:
                total_proventos_var += item["valor"]
            else:
                total_descontos_var += abs(item["valor"])

        st.markdown(f"*Total Proventos Variáveis:* R$ {total_proventos_var:.2f}")
        st.markdown(f"*Total Descontos Variáveis:* R$ {total_descontos_var:.2f}")

    # Cálculo final
    proventos = salario_base + total_proventos_var
    descontos_var = total_descontos_var
    inss = calcular_inss(proventos)
    base_ir = proventos - inss
    irrf = calcular_irrf(base_ir)
    descontos_totais = inss + irrf + descontos_var
    liquido = proventos - descontos_totais

    st.divider()
    st.subheader("Resumo Cálculo")
    st.write(f"*Proventos Totais:* R$ {proventos:.2f}")
    st.write(f"*INSS:* R$ {inss:.2f}")
    st.write(f"*Base IRRF:* R$ {base_ir:.2f}")
    st.write(f"*IRRF:* R$ {irrf:.2f}")
    st.write(f"*Descontos Variáveis:* R$ {descontos_var:.2f}")
    st.write(f"*Salário Líquido:* R$ {liquido:.2f}")

# Botão Gerar PDF (usa os valores calculados)
if st.button("Gerar Holerite em PDF"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(0, 10, f"Empresa: {nome_empresa} - CNPJ: {cnpj}", ln=1)
    pdf.cell(0, 10, f"Endereço: {endereco}", ln=1)
    pdf.ln(5)
    pdf.cell(0, 10, f"Funcionário: {nome_func} - CPF: {cpf}", ln=1)
    pdf.cell(0, 10, f"Cargo: {cargo} - Admissão: {data_adm}", ln=1)
    pdf.cell(0, 10, f"Competência: {mes_ano}", ln=1)
    pdf.ln(10)

    pdf.cell(0, 10, "Proventos", ln=1)
    pdf.cell(120, 8, "Salário Base", border=1)
    pdf.cell(70, 8, f"R$ {salario_base:.2f}", border=1, ln=1)

    for item in st.session_state.itens:
        if item["valor"] >= 0:
            pdf.cell(120, 8, item["descricao"], border=1)
            pdf.cell(70, 8, f"R$ {item['valor']:.2f}", border=1, ln=1)

    pdf.cell(120, 8, "Total Proventos", border=1)
    pdf.cell(70, 8, f"R$ {proventos:.2f}", border=1, ln=1)
    pdf.ln(5)

    pdf.cell(0, 10, "Descontos", ln=1)
    pdf.cell(120, 8, "INSS", border=1)
    pdf.cell(70, 8, f"R$ {inss:.2f}", border=1, ln=1)
    pdf.cell(120, 8, "IRRF", border=1)
    pdf.cell(70, 8, f"R$ {irrf:.2f}", border=1, ln=1)

    for item in st.session_state.itens:
        if item["valor"] < 0:
            pdf.cell(120, 8, item["descricao"], border=1)
            pdf.cell(70, 8, f"R$ {abs(item['valor']):.2f}", border=1, ln=1)

    pdf.cell(120, 8, "Total Descontos", border=1)
    pdf.cell(70, 8, f"R$ {descontos_totais:.2f}", border=1, ln=1)
    pdf.ln(10)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(120, 10, "Salário Líquido a Pagar", border=1)
    pdf.cell(70, 10, f"R$ {liquido:.2f}", border=1, ln=1)
    pdf.ln(20)

    pdf.set_font("Arial", size=10)
    pdf.cell(0, 10, "Assinatura do Funcionário: ___________ Data: _//_", ln=1)
    pdf.cell(0, 10, "Assinatura do Responsável: ___________ Data: _//_", ln=1)

    pdf_output = io.BytesIO(pdf.output(dest='S').encode('latin1'))
    pdf_output.seek(0)

    st.download_button(
        "Baixar Holerite PDF",
        pdf_output,
        file_name=f"holerite_{nome_func.replace(' ', '')}{mes_ano.replace('/', '_')}.pdf",
        mime="application/pdf"
    )
