from sqlmodel import Field, SQLModel, create_engine, text
from typing import Optional , Any
from contextlib import contextmanager
from datetime import datetime
from sqlalchemy import UniqueConstraint
from quadro_informativo.producer import ProducerQuadro
from datetime import datetime 
from loguru import logger  
from comum.config import DB_CONFIG

# Modelo correspondente à tabela existente
class Quadro_informativo(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("cod_pregao", "tipo", name="uq_cod_pregao_tipo"),
        )
    id: Optional[int] = Field(default=None, primary_key=True)
    cod_pregao: str
    tipo: str
    data_registro: datetime

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

def verificar_ultimo_status(cod_pregao: str, tipo: str) -> Optional[datetime]:
    try:
        with get_engine() as engine:
            with engine.connect() as conn:
                result = conn.execute(
                    text("""
                        SELECT data_registro FROM quadro_informativo 
                        WHERE cod_pregao = :cod_pregao AND tipo = :tipo
                        ORDER BY data_registro DESC LIMIT 1
                    """),
                    {'cod_pregao': cod_pregao, 'tipo': tipo}
                ).fetchone()
                return result[0] if result else None
    except Exception as e:
        print(f"Erro ao verificar último status: {e}")
        return None

def inserir_dados_pregao(dadosprg : dict[str, Any],cod_pregao: str, tipo: str, data_registro: datetime, texto: str = None) -> bool:
    try:
        ultimo_status = verificar_ultimo_status(cod_pregao, tipo)
        
        if ultimo_status and ultimo_status == data_registro:
            print(f"Status do tipo ({tipo}) do pregão {cod_pregao} não mudou.")
            return True
            
        with get_engine() as engine:
            with engine.connect() as conn:
                conn.execute(
                    text("""
                        INSERT INTO quadro_informativo 
                        (cod_pregao, tipo, data_registro) 
                        VALUES (:cod_pregao, :tipo, :data_registro)
                        ON CONFLICT ON CONSTRAINT uq_cod_pregao_tipo
                        DO UPDATE SET data_registro = EXCLUDED.data_registro
                    """),
                    {
                        'cod_pregao': cod_pregao,
                        'tipo': tipo,
                        'data_registro': data_registro
                    }
                )
                conn.commit()
                # Publicar atualização
                status_data = {
                    'dados_pregao': dadosprg,
                    'tipo': tipo,
                    'registro': texto if texto else [],
                    'data_registro':data_registro,
                    'ultima_verificacao_em': datetime.now()
                }
                
                try:
                    producer = ProducerQuadro()
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