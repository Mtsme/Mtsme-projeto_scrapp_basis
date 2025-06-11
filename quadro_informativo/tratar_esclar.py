from datetime import datetime
from typing import List
from pydantic import BaseModel
from quadro_informativo.config import inserir_dados_pregao
import json
from comum.models import DadosPregao


class Esclarecimento(BaseModel):
    data: datetime
    questionamento: str
    resposta: str
    cod_pregao: str

class Esclarecimentos(BaseModel):
    esclarecimentos: List[Esclarecimento]

def tratar_dados(dadosprg,dados_brutos):
    """
    Trata os dados coletados e retorna uma lista de objetos Esclarecimento.
    """
    esclarecimentos_validos = []

    for item in dados_brutos:
        try:
            esclarecimento = Esclarecimento(
                data=item.data,
                questionamento=item.questionamento,
                resposta=item.resposta,
                cod_pregao=item.codigo_prg
            )
            esclarecimentos_validos.append(esclarecimento)
            inserir_dados_pregao(
                dadosprg=dadosprg.model_dump(),
                cod_pregao=item.codigo_prg,
                tipo="ESCLARECIMENTO",
                data_registro=item.data,
                texto=f'questionamento:{json.dumps(item.questionamento)}resposta:{json.dumps(item.resposta)}'
            )
        except Exception as e:
            print(f"Erro ao processar item: {e}")

    return esclarecimentos_validos

def main1(dadosprg:DadosPregao,driver):
    url = f"https://cnetmobile.estaleiro.serpro.gov.br/comprasnet-web/public/compras/acompanhamento-compra?compra={dadosprg.codigo_prg}"
    # Importa a função diretamente aqui para evitar circularidade
    from coletar_esclar import coletar_esclarecimentos
    dados = coletar_esclarecimentos(url, dadosprg.codigo_prg,driver)
    
    if dados is not None: 
        if not dados:
            print('Nenhum esclarecimento a ser apresentado')
        else:
            esclarecimentos = tratar_dados(dadosprg,dados)
            resultado = Esclarecimentos(esclarecimentos=esclarecimentos).model_dump_json(indent=2)
            print(resultado)