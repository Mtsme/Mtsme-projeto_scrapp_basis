# config_info.py - correções
from sqlmodel import Field, SQLModel, create_engine, text
from typing import Optional , Any
from contextlib import contextmanager
import json
from sqlalchemy import UniqueConstraint
from pydantic import BaseModel
from propostas.anexos.producer_arquivo import ProducerArquivo
from datetime import datetime 
from loguru import logger  
from comum.config import DB_CONFIG

# Modelo correspondente à tabela existente
class Arquivos_propostas(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("cod_pregao", "grupo", "cnpj", name="uq_info"),
    )
    
    id: Optional[int] = Field(default=None, primary_key=True)
    cod_pregao: str = Field(index=True)
    grupo: str = Field(index=True)
    cnpj: str = Field(index=True)
    ultimo_arquivo: str
    

@contextmanager
def get_engine():
    engine = None
    try:
        engine = create_engine(
            f'postgresql+psycopg2://{DB_CONFIG["user"]}:{DB_CONFIG["password"]}@'
            f'{DB_CONFIG["host"]}:{DB_CONFIG["port"]}/{DB_CONFIG["dbname"]}',
            echo=True  # Habilita logging para debug
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
def verificar_ultimo_status(cod_pregao, grupo, cnpj, ultimo_arquivo=None) -> Optional[str]:
    try:
        with get_engine() as engine:
            with engine.connect() as conn:
                result = conn.execute(
                    text("""
                        SELECT ultimo_arquivo FROM arquivos_propostas
                        WHERE cod_pregao = :cod_pregao AND grupo = :grupo AND cnpj = :cnpj
                        ORDER BY id DESC LIMIT 1
                    """),
                    {'cod_pregao': cod_pregao, 'grupo': grupo, 'cnpj': cnpj, 'ultimo_arquivo': ultimo_arquivo}
                ).fetchone()
                return result[0] if result else None
    except Exception as e:
        print(f"Erro ao verificar último status: {e}")
        return None

def inserir_dados_pregao( dadospregao:dict[str, Any],cod_pregao, grupo, cnpj, ultimo_arquivo, lista_anexos: Optional[dict] = None) -> bool:
    try:
        with get_engine() as engine:
            with engine.connect() as conn:
                # Verificar se os dados já existem
                ultimo_status = verificar_ultimo_status(cod_pregao,grupo,cnpj,ultimo_arquivo)
                
                if ultimo_status and ultimo_arquivo and ultimo_status == ultimo_arquivo:
                    print(f"A ultima atualizacao de anexos do cnpj: ({cnpj}) no pregão {cod_pregao} NAO MUDOU.")
                    return True
                
                # Inserir ou atualizar os dados
                conn.execute(
                    text("""
                        INSERT INTO arquivos_propostas
                        (cod_pregao, grupo, cnpj, ultimo_arquivo) 
                        VALUES (:cod_pregao, :grupo, :cnpj, :ultimo_arquivo)
                        ON CONFLICT ON CONSTRAINT uq_info 
                        DO UPDATE SET ultimo_arquivo = EXCLUDED.ultimo_arquivo
                    """),
                    {
                        'cod_pregao': cod_pregao,
                        'grupo': grupo,
                        'cnpj': cnpj,
                        'ultimo_arquivo': ultimo_arquivo
                    }
                )
                conn.commit()
                
                # Publicar atualização
                status_data = {
                    'dados_pregao': dadospregao,
                    'grupo': grupo,
                    'cnpj': cnpj,
                    'ultimos_arquivos':lista_anexos if lista_anexos else [],
                    'ultima_verificacao_em': datetime.now()
                }
                
                try:
                    producer = ProducerArquivo()
                    if producer.publish_status_update(status_data):
                        logger.info(f"Status publicado para {cnpj}")
                        return True
                    else:
                        logger.error(f"Falha crítica ao publicar para {cnpj}")
                        return False
                except Exception as e:
                    logger.error(f"Erro no producer: {str(e)}")
                    return False
                
    except Exception as e:
        logger.error(f"Erro geral ao inserir dados: {str(e)}")
        return False