from pydantic import BaseModel

class DadosPregao(BaseModel):
    codigo_uasg: str
    numero_licitacao: str
    tipo_pregao: str = "E"
    uuid_processo: str | None = None
    id_pregao: int
    codigo_prg: str
    apelido: str
    sigla_sistema: str = "comprasnovo"
    # TODO verificar uso dos dois campos:
    id_sistema: int | None
    acompanhar: bool = True
