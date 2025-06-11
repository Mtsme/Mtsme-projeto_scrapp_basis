import sys
from typing import List

import undetected_chromedriver as uc
from loguru import logger
from result import Result, Ok, Err
from sqlalchemy.engine.base import Engine
from sqlmodel import Session, create_engine, select

from config import Config
from consumer import Consumer
from models import DadosMensagemBusca, MensagemPregao, DadosPregao, HistoricoMensagem, EventoPregao
from producer import Producer
from recupera_mensagens import BuscaMensagens

TIPO_EVENTO_MSG = 1

config: Config = Config()
producer: Producer = Producer(config)


def envia_mensagens(mensagens: List[MensagemPregao], dados_pregao: DadosPregao):
    evento = EventoPregao(tipo_evento=TIPO_EVENTO_MSG, mensagens_pregao=mensagens, dados_pregao=dados_pregao)
    json = evento.model_dump_json(indent=2, exclude={'mensagens_pregao': {-1: {'remetente'}}})
    logger.debug(json)
    producer.publish(json)


def atualiza_historico_mensagens(engine: Engine, codigo_prg: str, mensagem: MensagemPregao) -> None:
    with Session(engine) as session:
        historico_mensagem: HistoricoMensagem = session.exec(select(HistoricoMensagem)
                                                             .where(HistoricoMensagem.codigo_prg == codigo_prg)).first()
        if historico_mensagem:
            historico_mensagem.data_hora_mensagem = mensagem.data_hora
            historico_mensagem.remetente = mensagem.remetente
        else:
            historico_mensagem = HistoricoMensagem(codigo_prg=codigo_prg,
                                                   data_hora_mensagem=mensagem.data_hora,
                                                   remetente=mensagem.remetente)
        session.add(historico_mensagem)
        session.commit()


def callback(message: str) -> Result[bool, Exception]:
    retorno = Ok(True)
    main_driver = None
    engine: Engine | None = None
    try:
        engine = create_engine(config.db.url.__str__())
        dados_pregao = DadosPregao.model_validate_json(message)
        chrome_options = uc.ChromeOptions()
        chrome_options.accept_insecure_certs = True
        main_driver = uc.Chrome(options=chrome_options, advanced_elements=True)
        dados = DadosMensagemBusca(
            ultima_mensagem=get_ultima_mensagem(engine, dados_pregao.codigo_prg),
            cod_pregao_pesquisa=dados_pregao.codigo_prg)
        mensagens = BuscaMensagens().recupera_mensagens(main_driver, dados)
        if mensagens and len(mensagens):
            logger.debug(f'Enviando {len(mensagens)} mensagens para o pregão {dados_pregao.apelido}')
            envia_mensagens(mensagens, dados_pregao)
            atualiza_historico_mensagens(engine, dados_pregao.codigo_prg, mensagens[-1])
        else:
            logger.debug(f'Sem mensagens novas no pregão {dados_pregao.apelido}')
    except Exception as e:
        retorno = Err(e)
        logger.exception("Erro ao buscar mensagens!")
    finally:
        if main_driver:
            logger.debug('Fechando chromedriver')
            main_driver.quit()
        if engine:
            engine.dispose()
    return retorno


def get_ultima_mensagem(engine: Engine, codigo_prg: str) -> MensagemPregao | None:
    retorno = None
    with Session(engine) as session:
        historico_mensagem: HistoricoMensagem = session.exec(select(HistoricoMensagem)
                                                             .where(HistoricoMensagem.codigo_prg == codigo_prg)).first()
        if historico_mensagem:
            retorno = MensagemPregao(remetente=historico_mensagem.remetente, data_hora=historico_mensagem.data_hora_mensagem)
    return retorno


def start():
    logger.remove()
    logger.add(sys.stderr, level=config.default_log_level)
    consumer = Consumer(config)
    consumer.consume(callback)


if __name__ == '__main__':
    start()
