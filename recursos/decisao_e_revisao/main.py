import tempfile

from loguru import logger
from result import Result, Ok, Err

from comum.config import RabbitConfig, Config
from comum.consumer import Consumer
from comum.models import DadosPregao
from comum.uc_driver import cria_driver
from recursos.decisao_e_revisao.inicio import  extrair_dr

rabbit_config = RabbitConfig(fila_entrada='pregao-decisoes-revisoes')
consumer = Consumer(Config(rabbit=rabbit_config))
codigo_operacao = 'decisoes_revisoes'

def callback(message: str) ->  Result[bool, Exception]:
    retorno = Ok(True)
    main_driver = None
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            main_driver = cria_driver(temp_dir)
            dados_pregao = DadosPregao.model_validate_json(message)
            extrair_dr(main_driver,dados_pregao)
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


 
        

