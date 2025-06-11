import os
from sqlmodel import Field, SQLModel, create_engine, text
from typing import Optional
from contextlib import contextmanager
from sqlalchemy import UniqueConstraint
from pydantic import BaseModel
from downloads_compra.producer_arquivo import ProducerArquivo
from datetime import datetime 
from loguru import logger  
from comum.config import DB_CONFIG

# Modelo correspondente à tabela existente
class Arquivos_compra(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("cod_pregao" , name="uq_compra"),
    )
    
    id: Optional[int] = Field(default=None, primary_key=True)
    cod_pregao: str = Field(index=True)
    anexos: str = Field(index=True)

@contextmanager
def get_engine():
    engine = None
    try:
        engine = create_engine(
            f'postgresql+psycopg2://{DB_CONFIG["user"]}:{DB_CONFIG["password"]}@'
            f'{DB_CONFIG["host"]}:{DB_CONFIG["port"]}/{DB_CONFIG["dbname"]}' 
        )
        # Criar a tabela se não existir
        SQLModel.metadata.create_all(engine)
        yield engine
    except Exception as e:
        print(f"Erro de conexão com o banco: {e}")
        raise
    finally:
        if engine:
            engine.dispose()

# Modifique a função verificar_ultimo_status:
def verificar_ultimo_status(cod_pregao) -> Optional[str]:
    try:
        with get_engine() as engine:
            with engine.connect() as conn:
                result = conn.execute(
                    text("""
                        SELECT anexos FROM arquivos_compra
                        WHERE cod_pregao = :cod_pregao
                        ORDER BY id DESC LIMIT 1
                    """),
                    {'cod_pregao': cod_pregao}
                ).fetchone()
                return result[0] if result else None
    except Exception as e:
        print(f"Erro ao verificar último status: {e}")
        return None

def inserir_dados_pregao( dadospregao,cod_pregao,anexos,url_anexos:Optional[dict] = None) -> bool:
    try:
        with get_engine() as engine:
            with engine.connect() as conn:
                # Verificar se os dados já existem
                ultimo_status = verificar_ultimo_status(cod_pregao)
                
                if ultimo_status and anexos and ultimo_status == anexos:
                    print(f"A ultima atualizacao de anexos de compra do pregão {cod_pregao} NAO MUDOU.")
                    return True
                
                # Inserir ou atualizar os dados
                conn.execute(
                    text("""
                        INSERT INTO arquivos_compra
                        (cod_pregao, anexos) 
                        VALUES (:cod_pregao, :anexos)
                        ON CONFLICT (cod_pregao)
                        DO UPDATE SET anexos = EXCLUDED.anexos
                    """),
                    {
                        'cod_pregao': cod_pregao,
                        'anexos': anexos
                    }
                )
                conn.commit()
                
                # Publicar atualização
                status_data = {
                    'dados_pregao': dadospregao,
                    'local_anexos':url_anexos if url_anexos else [],
                    'ultima_verificacao_em': datetime.now()
                }
                
                try:
                    producer = ProducerArquivo()
                    if producer.publish_status_update(status_data):
                        logger.info(f"Status publicado para {cod_pregao}")
                        return True
                    else:
                        logger.error(f"Falha crítica ao publicar para {cod_pregao}")
                        return False
                except Exception as e:
                    logger.error(f"Erro no producer: {str(e)}")
                    return False
                
    except Exception as e:
        logger.error(f"Erro geral ao inserir dados: {str(e)}")
        return False