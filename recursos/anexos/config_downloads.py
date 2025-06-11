# config_info.py - correções
from sqlmodel import Field, SQLModel, create_engine, text
from typing import Optional, Any
from contextlib import contextmanager
from sqlalchemy import UniqueConstraint
from recursos.anexos.producer_downloads import ProducerArquivo
from datetime import datetime 
from loguru import logger 
from comum.config import DB_CONFIG 

# Modelo correspondente à tabela existente
class Arquivos_recursos(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("cod_pregao", "grupo", "cnpj", name="uq_arquivo"),
    ) 
    id: Optional[int] = Field(default=None, primary_key=True)
    cod_pregao: str = Field(index=True)
    grupo: str = Field(index=True)
    cnpj: str = Field(index=True)
    tipo: Optional [str] = Field(default=None)
    arquivos: Optional [str] = Field(default=None)
   

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
def verificar_ultimo_status(cod_pregao, grupo, cnpj ,arquivos , tipo=None) -> Optional[str]:
    try:
        with get_engine() as engine:
            with engine.connect() as conn:
                query = """
                    SELECT arquivos FROM arquivos_recursos
                    WHERE cod_pregao = :cod_pregao AND grupo = :grupo AND cnpj = :cnpj AND tipo = :tipo
                """
                params = {'cod_pregao': cod_pregao, 'grupo': grupo, 'cnpj': cnpj, 'tipo' :tipo, 'arquivos':arquivos}
                
                if tipo:
                    query += " AND tipo = :tipo"
                    params['tipo'] = tipo
                
                query += " ORDER BY id DESC LIMIT 1"
                
                result = conn.execute(text(query), params).fetchone()
                return result[0] if result else None
    except Exception as e:
        print(f"Erro ao verificar último status: {e}")
        return None

def inserir_dados_pregao( dadospregao: dict[str, Any],cod_pregao, grupo, cnpj, tipo, arquivos,localarquivos) -> bool:
    try:
        with get_engine() as engine:
            with engine.connect() as conn:
                # Verificar se os dados já existem
                ultimo_status = verificar_ultimo_status(cod_pregao,grupo,cnpj,tipo)
                
                if ultimo_status and arquivos and ultimo_status == arquivos:
                    print(f"A ultima atualizacao de anexos do cnpj: ({cnpj}) no pregão {cod_pregao} NAO MUDOU.")
                    return True
                
                # Inserir ou atualizar os dados
                conn.execute(
                    text("""
                        INSERT INTO arquivos_recursos
                        (cod_pregao, grupo, cnpj,tipo , arquivos) 
                        VALUES (:cod_pregao, :grupo, :cnpj, :tipo, :arquivos)
                        ON CONFLICT ON CONSTRAINT uq_arquivo 
                        DO UPDATE SET arquivos = EXCLUDED.arquivos
                    """),
                    {
                        'cod_pregao': cod_pregao,
                        'grupo': grupo,
                        'cnpj': cnpj,
                        'tipo':tipo,
                        'arquivos': arquivos
                    }
                )
                conn.commit()
                
                # Publicar atualização
                status_data = {
                    'dados_pregao': dadospregao,
                    'grupo': grupo,
                    'cnpj': cnpj,
                    'ultimo_arquivo':localarquivos if localarquivos else [],
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