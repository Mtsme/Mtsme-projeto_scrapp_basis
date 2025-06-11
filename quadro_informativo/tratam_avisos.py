# tratam_avisos.py
from datetime import datetime
from typing import List
from pydantic import BaseModel, ValidationError
from quadro_informativo.coletar_avisos import coletar_avisos
from quadro_informativo.config import inserir_dados_pregao
import json
from comum.models import DadosPregao


class Aviso(BaseModel):
    data: datetime
    aviso: str
    cod_pregao: str  

class Avisos(BaseModel):
    avisos: List[Aviso]

def tratar_dados(dadosprg,dados):
    """
    Trata os dados coletados e retorna uma lista de objetos Aviso.
    """
    avisos_validos = []

    for aviso in dados:
        try:
            data_convertida = datetime.strptime(aviso["data"], "%d/%m/%Y %H:%M")
            aviso_obj = Aviso(
                data=data_convertida,
                aviso=aviso["aviso"],
                cod_pregao=aviso["cod_pregao"]
            )
            avisos_validos.append(aviso_obj)
            
            # Mover a inserção para dentro do loop para cada aviso
            inserir_dados_pregao(
                dadosprg=dadosprg.model_dump(),
                cod_pregao=aviso_obj.cod_pregao,
                tipo="AVISO",
                data_registro=aviso_obj.data,
                texto=json.dumps(aviso_obj.aviso)
            )
        except ValidationError as e:
            print(f"Erro ao validar aviso: {e}")
        except ValueError as e:
            print(f"Erro ao converter data: {e}")
        except KeyError as e:
            print(f"Campo faltando no aviso: {e}")

    return avisos_validos

def main0(dadosprg:DadosPregao,driver):
    url = f"https://cnetmobile.estaleiro.serpro.gov.br/comprasnet-web/public/compras/acompanhamento-compra?compra={dadosprg.codigo_prg}"
    dados = coletar_avisos(url, dadosprg.codigo_prg,driver)
    
    if dados is None:
        print(f"Erro ao coletar dados para o pregão {dadosprg.codigo_prg}")
        return
    
    if not dados:
        print(f'Nenhum informativo a ser apresentado para o pregão {dadosprg.codigo_prg}')
    else:
        try:
            avisos = tratar_dados(dadosprg,dados)
            resultado = Avisos(avisos=avisos).model_dump_json(indent=2)
            
            print(resultado)
        except Exception as e:
            print(f"Erro ao processar avisos para {dadosprg.codigo_prg}: {e}")