from sqlmodel import Field, SQLModel, create_engine, text
from typing import Optional 
from contextlib import contextmanager
from sqlalchemy import UniqueConstraint
from info_pregao.producer import ProducerInfo
from info_pregao.models import Info
from datetime import datetime 
from loguru import logger 
from comum.config import DB_CONFIG
from comum.models import DadosPregao

# Modelo correspondente à tabela existente
class pregao_info_gerais(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("cod_prg", "periodo_entrega", "data_abertura","fase_contratacao", name="uq_info_gerais"),
    )
    
    id: Optional[int] = Field(default=None, primary_key=True)
    cod_prg:str =Field(index=True)
    fase_contratacao:str=Field(default=None,index=True)
    criterio_julgamento: str =Field(default=None)
    modo_disputa: str=Field(default=None)
    tipo_objeto: Optional[str] =Field(default=None)
    objeto: Optional[str] =Field(default=None)
    periodo_entrega: Optional[str]= Field(default=None,index=True)
    responsavel_compra: Optional[str]= Field(default=None)
    data_abertura: Optional[str] =Field(default=None,index=True)
    uf_uasg: Optional[str]= Field(default=None)
    id_pncp: Optional[str]=Field(default=None)

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

def verificar_ultimo_status(dados:Info) -> Optional[str]:
    try:
        with get_engine() as engine:
            with engine.connect() as conn:
                result = conn.execute(
                    text("""
                        SELECT fase_contratacao FROM pregao_info_gerais
                        WHERE cod_prg = :cod_prg AND periodo_entrega = :periodo_entrega AND data_abertura = :data_abertura
                        ORDER BY id DESC LIMIT 1
                    """),
                    {'cod_prg':dados.cod_prg ,'periodo_entrega':dados.periodo_entrega, 'data_abertura': dados.data_abertura, 'fase_contratacao' :dados.fase_contratacao}
                ).fetchone()
                return result[0] if result else None
    except Exception as e:
        print(f"Erro ao verificar último status: {e}")
        return None

# config_dr.py - correções
def inserir_dados_pregao(dados_info:Info,dadosprg:DadosPregao) -> bool:
    try:  # Corrigido: indentação do try
        with get_engine() as engine:
            with engine.connect() as conn:
                # Verificar se os dados já existem
                ultimo_status = verificar_ultimo_status(dados_info)
                
                if ultimo_status and ultimo_status == dados_info.fase_contratacao:
                    print(f"A data de abertura no pregão {dados_info.cod_prg} não mudaram.")
                    return True
                
                # Inserir ou atualizar os dados
                trans = conn.begin()
                try:
                    conn.execute(
                        text("""
                            INSERT INTO pregao_info_gerais
                            (cod_prg,fase_contratacao,criterio_julgamento,modo_disputa, tipo_objeto,objeto,periodo_entrega,responsavel_compra,data_abertura,uf_uasg,id_pncp) 
                            VALUES (:cod_prg, :fase_contratacao, :criterio_julgamento, :modo_disputa, :tipo_objeto, :objeto, :periodo_entrega, :responsavel_compra, :data_abertura, :uf_uasg, :id_pncp)
                            ON CONFLICT ON CONSTRAINT uq_info_gerais
                            DO UPDATE SET fase_contratacao = EXCLUDED.fase_contratacao
                        """),
                        {
                            
                            'cod_prg': dados_info.cod_prg,
                            'fase_contratacao':dados_info.fase_contratacao,
                            'criterio_julgamento':dados_info.criterio_julgamento,
                            'modo_disputa':dados_info.modo_disputa,
                            'tipo_objeto':dados_info.tipo_objeto,
                            'objeto':dados_info.objeto,
                            'periodo_entrega':dados_info.periodo_entrega,
                            'responsavel_compra':dados_info.responsavel_compra,
                            'data_abertura':dados_info.data_abertura,
                            'uf_uasg':dados_info.uf_uasg,
                            'id_pncp':dados_info.id_pncp
                        }
                    )
                    trans.commit()
                    logger.info("Dados inseridos/atualizados com sucesso")
                except Exception as e:
                    trans.rollback()
                    logger.error(f"Erro na transação: {e}")
                    raise

                status_data = {
                    'dados_pregao':dadosprg.model_dump(),
                    'fase_contratacao':dados_info.fase_contratacao,
                    'criterio_julgamento':dados_info.criterio_julgamento,
                    'modo_disputa':dados_info.modo_disputa,
                    'tipo_objeto':dados_info.tipo_objeto,
                    'objeto':dados_info.objeto,
                    'periodo_entrega':dados_info.periodo_entrega,
                    'responsavel_compra':dados_info.responsavel_compra,
                    'data_abertura':dados_info.data_abertura,
                    'uf_uasg':dados_info.uf_uasg,
                    'id_pncp':dados_info.id_pncp,
                    'ultima_verificacao_em': datetime.now().isoformat() 
                }
                producer = ProducerInfo()
                if producer.publish_status_update(status_data):
                    logger.success(f"Status publicado com sucesso")
                
                return True
                
    except Exception as e:
        logger.error(f"Erro ao inserir/atualizar: {e}")
        return False
                
    except Exception as e:
        print(f"Erro ao inserir dados: {e}")
        return False