from sqlmodel import Field, SQLModel, create_engine, text
from typing import Optional, Any
from contextlib import contextmanager
from propostas.status_licitante.producer_status import ProducerStatus
from pydantic import BaseModel
from datetime import datetime 
from sqlalchemy import UniqueConstraint
from loguru import logger 
from comum.config import DB_CONFIG

class RabbitConfigStatus(BaseModel):
    url: str = 'amqp://guest:guest@localhost:5672/'
    exchange: str = 'proposta.status.licitante'
    routing_key: str = '#'

class Status_licitante(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("cod_pregao", "grupo", "cnpj", name="uq_status"),
    )
    
    id: Optional[int] = Field(default=None, primary_key=True)
    cod_pregao: str = Field(index=True)
    grupo: str = Field(index=True)
    cnpj: str = Field(index=True)
    status: Optional[str] = Field(default=None)
    motivo: Optional[str] = Field(default=None)

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
        logger.error(f"Erro de conexão com o banco: {e}")  # Corrigido para usar logger
        raise
    finally:
        if engine:
            engine.dispose()

def verificar_ultimo_status(cod_pregao: str, grupo: str, cnpj: str) -> Optional[str]:
    try:
        with get_engine() as engine:
            with engine.connect() as conn:
                result = conn.execute(
                    text("""
                        SELECT status FROM status_licitante
                        WHERE cod_pregao = :cod_pregao AND grupo = :grupo AND cnpj = :cnpj
                        ORDER BY id DESC LIMIT 1
                    """),
                    {'cod_pregao': cod_pregao, 'grupo': grupo, 'cnpj': cnpj}
                ).fetchone()
                return result[0] if result else None
    except Exception as e:
        logger.error(f"Erro ao verificar último status: {e}")  # Corrigido para usar logger
        return None

def inserir_status_pregao(dadospregao: dict[str, Any],cod_pregao: str, grupo: str, cnpj: str,
                         status: Optional[str] = None, motivo: Optional[str] = None) -> bool:
    try:
        logger.info(f"Iniciando inserção de status para CNPJ: {cnpj}")
        
        with get_engine() as engine:
            with engine.connect() as conn:
                # Verificar último status com mais logs
                logger.debug(f"Verificando último status para {cnpj}")
                ultimo_status = verificar_ultimo_status(cod_pregao, grupo, cnpj)
                logger.debug(f"Último status encontrado: {ultimo_status}")
                
                if ultimo_status and ultimo_status == status:
                    logger.info(f"Status inalterado para CNPJ {cnpj} no pregão {cod_pregao}")
                    return True
                
                # Inserir ou atualizar com transação explícita
                trans = conn.begin()
                try:
                    logger.debug("Executando INSERT/UPDATE")
                    conn.execute(
                        text("""
                            INSERT INTO status_licitante
                            (cod_pregao, grupo, cnpj, status, motivo) 
                            VALUES (:cod_pregao, :grupo, :cnpj, :status, :motivo)
                            ON CONFLICT ON CONSTRAINT uq_status 
                            DO UPDATE SET 
                                status = EXCLUDED.status,
                                motivo = EXCLUDED.motivo
                        """),
                        {
                            'cod_pregao': cod_pregao,
                            'grupo': grupo,
                            'cnpj': cnpj,
                            'status': status,
                            'motivo': motivo
                        }
                    )
                    trans.commit()
                    logger.info("Dados inseridos/atualizados com sucesso")
                except Exception as e:
                    trans.rollback()
                    logger.error(f"Erro na transação: {e}")
                    raise
                
                # Publicar atualização
                # Corrigir a construção do status_data na função inserir_status_pregao
                
                status_data = {
                    'dados_pregao': dadospregao,
                    'grupo': grupo,
                    'cnpj': cnpj,
                    'status_antigo': ultimo_status,
                    'status_novo': status,
                    'motivo': motivo,
                    'ultima_verificacao_em': datetime.now().isoformat() 
                }
                producer = ProducerStatus()
                if producer.publish_status_update(status_data):
                    logger.success(f"Status publicado com sucesso para {cnpj}")
                
                return True
                
    except Exception as e:
        logger.error(f"Erro ao inserir/atualizar dados para CNPJ {cnpj}: {e}")
        return False