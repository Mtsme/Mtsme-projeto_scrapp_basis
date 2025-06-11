import tempfile

from loguru import logger
from result import Result, Ok, Err

from comum.config import RabbitConfig, Config
from comum.consumer import Consumer
from comum.models import DadosPregao
from comum.uc_driver import cria_driver
from propostas.dados_gerais.scraper import coletar_propostas_pregao

rabbit_config = RabbitConfig(fila_entrada='pregao-dados-propostas')
consumer = Consumer(Config(rabbit=rabbit_config))
codigo_operacao='dados_propostas'

def callback(message: str) ->  Result[bool, Exception]:
    retorno = Ok(True)
    main_driver = None
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            main_driver = cria_driver(temp_dir)
            dados_pregao = DadosPregao.model_validate_json(message)
            coletar_propostas_pregao(dados_pregao,main_driver,temp_dir)
    except Exception as e:
        retorno = Err(e)
        logger.exception("Erro ao buscar mensagens!")
    finally:
        if main_driver:
            logger.debug('Fechando chromedriver')
            main_driver.quit()
    return retorno

def main():
    consumer.consume(callback,codigo_operacao)


