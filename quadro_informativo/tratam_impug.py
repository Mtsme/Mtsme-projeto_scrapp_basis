import re
from datetime import datetime
from typing import List
from pydantic import BaseModel, ValidationError
from quadro_informativo.coletar_impug import coletar_impug
from quadro_informativo.config import inserir_dados_pregao
import json
from comum.models import DadosPregao

# Modelo Pydantic para impugnações
class Impugnacao(BaseModel):
    data: datetime
    impugnacao: str
    cod_pregao: str  

# Modelo container para a lista completa
class Impugnacoes(BaseModel):
    impugnacoes: List[Impugnacao]

def processar_impugnacao(dadosprg,impugna: str, cod_pregao: str) -> List[Impugnacao]:  # Adicionado parâmetro cod_pregao
    """
    Processa a string de impugnações e retorna lista validada
    """
    pattern = r"(\d{2}/\d{2}/\d{4} \d{2}:\d{2})\s+(.*?)(?=\d{2}/\d{2}/\d{4} \d{2}:\d{2}|$)"
    matches = re.findall(pattern, impugna, re.DOTALL)
    
    impugnacoes = []
    for match in matches:
        try:
            data_convertida = datetime.strptime(match[0], "%d/%m/%Y %H:%M")
            impugnacao_obj = Impugnacao(
                data=data_convertida,
                impugnacao=match[1].strip(),
                cod_pregao=cod_pregao 
            )
            impugnacoes.append(impugnacao_obj)
            inserir_dados_pregao(
                dadosprg=dadosprg.model_dump(),
                cod_pregao=impugnacao_obj.cod_pregao,
                tipo="IMPUGNACAO",
                data_registro=impugnacao_obj.data,
                texto=json.dumps(impugnacao_obj.impugnacao)
            )
        except (ValidationError, ValueError) as e:
            print(f"Erro ao processar item: {e}")
    
    return impugnacoes

def main2(dadosprg:DadosPregao,driver):
    url = f"https://cnetmobile.estaleiro.serpro.gov.br/comprasnet-web/public/compras/acompanhamento-compra?compra={dadosprg.codigo_prg}"
    impug_text = coletar_impug(url,driver)
    
    if impug_text is not None:  # None indica erro
        if not impug_text:  # String vazia indica "sem impugnações"
            print(f'Nenhuma impugnação a ser apresentada para o pregao: {dadosprg.codigo_prg}')
        else:
            try:
                impugnacoes = processar_impugnacao(dadosprg,impug_text, dadosprg.codigo_prg)  # Passando codigo_prg
                resultado = Impugnacoes(impugnacoes=impugnacoes).model_dump_json(indent=2)
                print(resultado)
            except ValidationError as e:
                print(f"Erro na estrutura dos dados: {e}")
