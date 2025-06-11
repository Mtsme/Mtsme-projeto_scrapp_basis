from decimal import Decimal, InvalidOperation

def parse_decimal(valor_str: str) -> Decimal | None:
    valor_str = valor_str.replace("R$", "").strip()
    
    # Trata explicitamente valores inválidos como '-' ou vazio
    if valor_str in ('-', ''):
        return None
    
    # converte as string que tem o valor para decimal
    # retira R$ virgula e pontos
    if ',' in valor_str:
        parte_inteira, parte_decimal = valor_str.split(',', 1)
        parte_inteira = parte_inteira.replace(".", "")
        valor_normalizado = f"{parte_inteira}.{parte_decimal}"
    else:
        valor_normalizado = valor_str.replace(".", "")
    
    try:
        return Decimal(valor_normalizado)
    except InvalidOperation as e:
        print(f"Erro ao converter '{valor_str}': {e}")
        return None  # Retorna None para manter consistência