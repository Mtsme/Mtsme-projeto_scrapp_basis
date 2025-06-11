from pydantic import BaseModel
from datetime import datetime

class Info(BaseModel):
    cod_prg:str
    fase_contratacao:str| None = None
    criterio_julgamento: str| None = None
    modo_disputa: str| None = None
    tipo_objeto: str| None = None
    objeto: str| None = None
    periodo_entrega: str| None = None
    responsavel_compra: str | None = None
    data_abertura: str| None = None
    uf_uasg: str| None = None
    id_pncp: str| None = None
