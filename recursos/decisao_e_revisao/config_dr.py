from sqlmodel import Field, SQLModel, create_engine, text
from typing import Optional , Any
from contextlib import contextmanager
import json
from sqlalchemy import UniqueConstraint
from recursos.decisao_e_revisao.producer_dr import ProducerDR
from pydantic import BaseModel
from datetime import datetime 
from loguru import logger 
from comum.config import DB_CONFIG

class RabbitConfigStatus(BaseModel):
    url: str = 'amqp://guest:guest@localhost:5672/'
    exchange: str = 'recursos.decisao.revisao'
    routing_key: str = '#'


# Modelo correspondente à tabela existente
class decisoes_revisoes(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("cod_pregao", "grupo", "secao", "tipo", name="uq_dr"),
    )
    
    id: Optional[int] = Field(default=None, primary_key=True)
    grupo:str =Field(index=True)
    secao:str =Field(index=True)
    cod_pregao: str = Field(index=True)
    tipo: str = Field(index=True)

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

def verificar_ultimo_status( cod_pregao: str, grupo:str, secao:str, tipo: str) -> Optional[str]:
    try:
        with get_engine() as engine:
            with engine.connect() as conn:
                result = conn.execute(
                    text("""
                        SELECT tipo FROM decisoes_revisoes
                        WHERE cod_pregao = :cod_pregao AND grupo =:grupo AND secao =: secao AND tipo =: tipo
                        ORDER BY id DESC LIMIT 1
                    """),
                    {'cod_pregao': cod_pregao,'grupo':grupo, 'secao':secao, 'tipo' : tipo}
                ).fetchone()
                return result[0] if result else None
    except Exception as e:
        print(f"Erro ao verificar último status: {e}")
        return None

# config_dr.py - correções
def inserir_dados_pregao(dadospregao:dict[str, Any] ,grupo:str, secao:str,cod_pregao: str, tipo: str,dados:str) -> bool:
    try:  # Corrigido: indentação do try
        with get_engine() as engine:
            with engine.connect() as conn:
                # Verificar se os dados já existem
                ultimo_status = verificar_ultimo_status(cod_pregao,grupo,secao, tipo)
                
                if ultimo_status and ultimo_status == tipo:
                    print(f"Os dados do tipo ({tipo}) no pregão {cod_pregao} não mudaram.")
                    return True
                
                # Inserir ou atualizar os dados
                trans = conn.begin()
                try:
                    conn.execute(
                        text("""
                            INSERT INTO decisoes_revisoes 
                            (grupo, secao, cod_pregao, tipo) 
                            VALUES (:grupo, :secao, :cod_pregao, :tipo)
                            ON CONFLICT ON CONSTRAINT uq_dr 
                            DO UPDATE SET tipo = EXCLUDED.tipo
                        """),
                        {
                            
                            'cod_pregao': cod_pregao,
                            'grupo':grupo,
                            'secao': secao,
                            'tipo': tipo
                        }
                    )
                    trans.commit()
                    logger.info("Dados inseridos/atualizados com sucesso")
                except Exception as e:
                    trans.rollback()
                    logger.error(f"Erro na transação: {e}")
                    raise

                status_data = {
                    'dados_pregao':dadospregao,
                    'grupo': grupo,
                    'secao':secao,
                    'tipo':tipo,
                    'dados': json.dumps(dados),
                    'ultima_verificacao_em': datetime.now().isoformat() 
                }
                producer = ProducerDR()
                if producer.publish_status_update(status_data):
                    logger.success(f"Status publicado com sucesso para pregao {cod_pregao}")
                
                return True
                
    except Exception as e:
        logger.error(f"Erro ao inserir/atualizar dados para pregao {cod_pregao}: {e}")
        return False
                
    except Exception as e:
        print(f"Erro ao inserir dados: {e}")
        return False