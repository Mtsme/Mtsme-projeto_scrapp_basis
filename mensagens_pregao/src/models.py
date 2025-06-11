from datetime import datetime
from typing import List

from pydantic import BaseModel, computed_field
from sqlmodel import SQLModel, Field, String

def get_tipo_remetente(remetente: str) -> int | None:
    retorno = None
    remetente_lower = remetente.lower()
    if 'pregoeiro' in remetente_lower:
        retorno = 3
    elif 'participante' in remetente_lower:
        retorno = 1
    elif 'sistema' in remetente_lower:
        retorno = 2
    return retorno


class HistoricoMensagem(SQLModel, table=True):
    __tablename__ = "historico_mensagem"
    id: int | None = Field(default=None, primary_key=True)
    codigo_prg: str = Field(default=None, unique=True, max_length=64, sa_type=String(64))
    remetente: str | None = Field(default=None, max_length=255, sa_type=String(255))
    data_hora_mensagem: datetime


class MensagemPregao(BaseModel):
    remetente: str
    item: str | None = None
    texto: str | None = None
    data_hora: datetime

    @computed_field
    def tipo_remetente(self) -> int | None:
        retorno = None
        if self.remetente:
            retorno = get_tipo_remetente(self.remetente)
        return retorno

    def is_mesmo_data_remetente(self, other: 'MensagemPregao') -> bool:
        return other and self.remetente == other.remetente and self.data_hora == other.data_hora


class DadosMensagemBusca(BaseModel):
    ultima_mensagem: MensagemPregao | None
    cod_pregao_pesquisa: str


class DadosPregao(BaseModel):
    codigo_uasg: str
    numero_licitacao: str
    tipo_pregao: str = "E"
    uuid_processo: str | None = None
    id_pregao: int
    codigo_prg: str
    apelido: str
    sigla_sistema: str = "comprasnovo"


class EventoPregao(BaseModel):
    tipo_evento: int
    mensagens_pregao: List[MensagemPregao]
    dados_pregao: DadosPregao
