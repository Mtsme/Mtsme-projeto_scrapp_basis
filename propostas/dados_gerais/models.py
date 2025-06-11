from decimal import Decimal
from pydantic import BaseModel
from typing import Optional



# classe oferta para pegar as informações dos serviços oferecidos
class OfertaItem(BaseModel):
    item: str
    valor_ofertado_unit: Decimal
    valor_negociado_unit: Decimal | None = None


# informacoes gerais da proposta de cada empresa
class Proposta(BaseModel):
    cod_prg:str
    cnpj: str
    tipo: str | None = None      # microempresa ou pequeno porte
    situacao: str | None = None  # desclassificada, inabilitada ou adjudicada
    nome: str
    uf: str
    ofertado: Decimal           # valor ofertado pela empresa
    negociado: Decimal | None = None
    motivo: str | None = None     # motivo da desclassificação/inabilitação
    oferta_itens: list[OfertaItem] = []
    anexos:list=[]
    temp_dir : str
    

    def adicionar_itens(self, oferta_item: OfertaItem):
        self.oferta_itens.append(oferta_item)

# qual grupo da proposta
class GrupoPropostas(BaseModel):
    num_grupo: str
    propostas: list[Proposta] = []

# agrupa todas as propostas por pregao
class PropostaPregao(BaseModel):
    codigo_prg: str
    grupos: list[GrupoPropostas] = []

    def adicionar_grupo(self, grupo: GrupoPropostas):
        self.grupos.append(grupo)

# classe que representa o modelo de mensagem que vem do rabbitmq
class EventoPregao(BaseModel):
    codigo_uasg: str
    apelido: str
    id_pregao: int
    codigo_prg: str
    numero_licitacao: str
    id_sistema: int
    acompanhar: bool

class EventoStatus(BaseModel):
    cod_pregao: str
    grupo: str
    cnpj: str
    ultimo_arquivo: Optional[str] = None

class DadosPregao(BaseModel):
    codigo_uasg: str
    apelido: str
    id_pregao: int
    codigo_prg: str
    numero_licitacao: str
    id_sistema: int
    acompanhar: bool
