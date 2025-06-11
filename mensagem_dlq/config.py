import json
from sqlalchemy.dialects.postgresql import JSONB 
from sqlmodel import Field, SQLModel, create_engine, text, Column 
from typing import Optional, Dict, Any
from datetime import datetime
from loguru import logger
from comum.config import DB_CONFIG
from comum.models import DadosPregao 

class Historico_de_erro(SQLModel, table=True):
    __tablename__ = "historico_de_erros" 

    id: Optional[int] = Field(default=None, primary_key=True) 
    cod_prg:Optional[str] = Field(default=None) 
    x_error_msg: Optional[str] = Field(default=None)
    x_error_class: Optional[str] = Field(default=None)
    x_error_date: Optional[datetime] = Field(default=None) 
    x_instance_name: Optional[str] = Field(default=None) 
    x_source_queue: Optional[str] = Field(default=None) 
    payload:Optional[str] = Field(default=None) 
    payload_json: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSONB)) 


def get_engine():
    engine = None
    try:
        engine = create_engine(
            f'postgresql+psycopg2://{DB_CONFIG["user"]}:{DB_CONFIG["password"]}@' 
            f'{DB_CONFIG["host"]}:{DB_CONFIG["port"]}/{DB_CONFIG["dbname"]}'
        )
        return engine
    except KeyError as e:
        logger.error(f"Chave de configuração do banco ausente em DB_CONFIG: {e}") 
        raise
    except Exception as e:
        logger.error(f"Erro de conexão com o banco: {e}") 
        raise

def _ensure_tables_created():
    engine = None
    try:
        engine = get_engine() 
        SQLModel.metadata.create_all(engine) 
        logger.info("Validação/Criação de tabelas (SQLModel.metadata.create_all) executada com sucesso.")
    except Exception as e:
        logger.error(f"Erro ao garantir criação de tabelas: {e}") 
        raise 
    finally:
        if engine:
            engine.dispose() 
            
_ensure_tables_created() 

def inserir_historico(dados: Historico_de_erro, payload: str, payload_json: Optional[DadosPregao]) -> bool:
    engine = None
    try:
        logger.info(f"Iniciando inserção de histórico de erro")
        engine = get_engine() 

        with engine.connect() as conn:
            trans = conn.begin() 
            try:
                logger.debug("Executando INSERT em historico_de_erros") 
                
                payload_json_dmp = payload_json.model_dump() if payload_json else None
                payload_json_str_for_db = None
                if payload_json_dmp is not None:
                    payload_json_str_for_db = json.dumps(payload_json_dmp)

                conn.execute(
                    text("""
                        INSERT INTO historico_de_erros
                        (cod_prg, x_error_msg, x_error_class, x_error_date, x_instance_name, x_source_queue, payload, payload_json)
                        VALUES (:cod_prg, :x_error_msg, :x_error_class, :x_error_date, :x_instance_name, :x_source_queue, :payload_str, :payload_json_data)
                    """), 
                    {
                        'cod_prg': payload_json.codigo_prg if payload_json else None, 
                        'x_error_msg': dados.x_error_msg, 
                        'x_error_class': dados.x_error_class, 
                        'x_error_date': dados.x_error_date, 
                        'x_instance_name': dados.x_instance_name, 
                        'x_source_queue': dados.x_source_queue, 
                        'payload_str': payload, 
                        'payload_json_data': payload_json_str_for_db 
                    }
                )
                trans.commit() 
                logger.info("Dados de histórico de erro inseridos com sucesso") 
                return True
            except Exception as e:
                trans.rollback()
                logger.error(f"Erro na transação ao inserir histórico de erro: {e}")
                raise
    except Exception as e:
        logger.error(f"Erro ao inserir histórico de erro (engine/setup ou falha na transação): {e}") 
        raise 
    finally:
        if engine:
            engine.dispose() 
            logger.debug("Engine do banco de dados para histórico de erro desmobilizado.") 