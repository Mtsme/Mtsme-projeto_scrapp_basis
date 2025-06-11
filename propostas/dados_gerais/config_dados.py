# config_dados.py - Versão corrigida
from sqlmodel import Field, SQLModel, create_engine, text
from typing import Optional, List , Any
from contextlib import contextmanager
from propostas.dados_gerais.producer_dados import ProducerStatus  
from pydantic import BaseModel
from datetime import datetime 
from sqlalchemy import UniqueConstraint
from loguru import logger  
from decimal import Decimal 
from comum.config import DB_CONFIG

class RabbitConfigdados(BaseModel):
    url: str = 'amqp://guest:guest@localhost:5672/'
    exchange: str = 'proposta.dados'
    routing_key: str = '#'

class Dados_propostas(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("cod_pregao", "grupo", "cnpj", name="uq_dados"),
    )
    
    id: Optional[int] = Field(default=None, primary_key=True)
    cod_pregao: str = Field(index=True)
    grupo: str = Field(index=True)
    cnpj: str = Field(index=True)      
    negociado: Optional[Decimal] = Field(default=None)
@contextmanager
def get_engine():
    engine = None
    try:
        engine = create_engine(
            f'postgresql+psycopg2://{DB_CONFIG["user"]}:{DB_CONFIG["password"]}@'
            f'{DB_CONFIG["host"]}:{DB_CONFIG["port"]}/{DB_CONFIG["dbname"]}',
            echo=True
        )
        SQLModel.metadata.create_all(engine)
        yield engine
    except Exception as e:
        logger.error(f"Erro de conexão com o banco: {e}")
        raise
    finally:
        if engine:
            engine.dispose()

def verificar_ultimo_status(cod_pregao: str, grupo: str, cnpj: str) -> Optional[Decimal]:
    try:
        with get_engine() as engine:
            with engine.connect() as conn:
                result = conn.execute(
                    text("""
                        SELECT negociado FROM dados_propostas
                        WHERE cod_pregao = :cod_pregao AND grupo = :grupo AND cnpj = :cnpj
                        ORDER BY id DESC LIMIT 1
                    """),
                    {'cod_pregao': cod_pregao, 'grupo': grupo, 'cnpj': cnpj}
                ).fetchone()
                return result if result else None
    except Exception as e:
        logger.error(f"Erro ao verificar último status: {e}")
        return None

def inserir_status_pregao(
    dadosprg: dict[str, Any],
    cod_pregao: str,
    grupo: str,
    cnpj: str,
    nome: str,
    uf: str,
    tipo: str,
    situacao: str,
    ofertado: str,
    negociado: Optional[Decimal] = None,
    motivo: Optional [str]=None,
    oferta_itens: Optional[List[dict]] = None
) -> bool:
    try:
        logger.info(f"Iniciando inserção de dados para CNPJ: {cnpj}")
        
        with get_engine() as engine:
            with engine.connect() as conn:
                ultimo_status = verificar_ultimo_status(cod_pregao, grupo, cnpj)
                logger.debug(f"Último status encontrado: {ultimo_status}")
                
                if ultimo_status and ultimo_status == negociado:
                    logger.info(f"Valor negociado inalterado para CNPJ {cnpj}")
                    return True
                
                trans = conn.begin()
                try:
                    conn.execute(
                        text("""
                            INSERT INTO dados_propostas
                            (cod_pregao, grupo, cnpj, negociado) 
                            VALUES (:cod_pregao, :grupo, :cnpj,:negociado)
                            ON CONFLICT ON CONSTRAINT uq_dados 
                            DO UPDATE SET 
                                negociado = EXCLUDED.negociado
                        """),
                        {
                            'cod_pregao': cod_pregao,
                            'grupo': grupo,
                            'cnpj': cnpj,
                            'negociado': negociado,}
                    )
                    trans.commit()
                    logger.info("Dados inseridos/atualizados com sucesso")
                except Exception as e:
                    trans.rollback()
                    logger.error(f"Erro na transação: {e}")
                    raise
                
                propostas_serializaveis = []
                if oferta_itens:
                    for item in oferta_itens:
                        propostas_serializaveis.append({
                            "item": item.item,
                            "valor_ofertado_unit": str(item.valor_ofertado_unit),
                            "valor_negociado_unit": str(item.valor_negociado_unit) if item.valor_negociado_unit else None,
                        })
                
                # Prepara os dados para o RabbitMQ
                status_data = {
                    'dados_pregao': dadosprg,
                    'grupo': grupo,
                    'cnpj': cnpj,
                    'tipo': tipo,
                    'status': situacao,
                    'motivo': motivo,
                    'nome': nome,
                    'uf': uf,
                    'valor_ofertado': str(ofertado) if ofertado else None,
                    'valor_negociado_antigo': str(ultimo_status[0]) if ultimo_status else 'sem valores',
                    'valor_negociado_atual': str(negociado) if negociado else None,
                    'propostas': propostas_serializaveis,  # Já serializado
                    'ultima_verificacao_em': datetime.now().isoformat()
                }
                
                producer = ProducerStatus()
                if producer.publish_status_update(status_data):
                    logger.success(f"Status publicado com sucesso para {cnpj}")
                
                return True
                
    except Exception as e:
        logger.error(f"Erro ao inserir/atualizar dados para CNPJ {cnpj}: {e}")
        return False