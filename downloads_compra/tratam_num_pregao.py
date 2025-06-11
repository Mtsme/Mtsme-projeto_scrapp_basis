from pydantic import BaseModel
from typing import Optional
from downloads_compra.num_pregao import coletar_pregao_orgao
import json

class PregaoInfo(BaseModel):
    numero_pregao: str  # Formato "90001/2025"
    orgao: str          # Formato completo "UASG 114702 - ENAP-ESCOLA NACIONAL DE ADM.PUBLICA/DF"

def tratar_dados_pregao(dados_brutos: str) -> Optional[PregaoInfo]:
    """
    Processa os dados brutos do pregão dividindo conforme solicitado:
    - numero_pregao: "90001/2025"
    - orgao: "UASG 114702 - ENAP-ESCOLA NACIONAL DE ADM.PUBLICA/DF"
    """
    if not dados_brutos:
        return None
        
    try:
        linhas = [linha.strip() for linha in dados_brutos.split("\n") if linha.strip()]
        
        # Extrai número do pregão (90001/2025)
        numero_pregao = linhas[0].split("N° ")[1].split(" (")[0].strip()
        
        # Pega a linha completa do órgão
        orgao = linhas[1].strip()
        
        return PregaoInfo(
            numero_pregao=numero_pregao,
            orgao=orgao
        )
        
    except Exception as e:
        print(f"Erro ao tratar dados do pregão: {e}")
        return None

def processar_pregao(codigo_prg: str, driver) -> Optional[str]:
    """
    Função principal para processar um pregão e retornar JSON
    """
    dados_brutos = coletar_pregao_orgao(codigo_prg, driver)
    if not dados_brutos:
        print("Falha ao coletar dados brutos")
        return None

    dados_tratados = tratar_dados_pregao(dados_brutos)
    if not dados_tratados:
        print("Falha ao tratar dados do pregão")
        return None

    try:
        resultado = dados_tratados.model_dump_json(indent=2)
    except AttributeError:
        resultado = json.dumps(dados_tratados.model_dump(), indent=2, ensure_ascii=False)
    
    print(resultado)

    return resultado
