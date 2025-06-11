import tempfile

from loguru import logger
from result import Result, Ok, Err

from comum.config import RabbitConfig, Config
from comum.consumer import Consumer
from comum.models import DadosPregao
from comum.uc_driver import cria_driver
from quadro_informativo.tratam_avisos import main0
from quadro_informativo.tratam_impug import main2
from quadro_informativo.tratar_esclar import main1

rabbit_config = RabbitConfig(fila_entrada='pregao-quadro-informativo')
consumer = Consumer(Config(rabbit=rabbit_config))
codigo_operacao='quadro_informativo'

def callback(message: str) ->  Result[bool, Exception]:
    retorno = Ok(True)
    main_driver = None
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            main_driver = cria_driver(temp_dir)
            dados_pregao = DadosPregao.model_validate_json(message)
            main0(dados_pregao,main_driver)
            main1(dados_pregao,main_driver)
            main2(dados_pregao,main_driver)
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
