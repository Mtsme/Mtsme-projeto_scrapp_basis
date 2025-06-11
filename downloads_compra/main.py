import tempfile

from loguru import logger
from result import Result, Ok, Err

from comum.config import RabbitConfig, Config
from comum.consumer import Consumer
from comum.models import DadosPregao
from comum.uc_driver import cria_driver
from downloads_compra.mover_downloads import baixar_e_organizar
from downloads_compra.tratam_num_pregao import processar_pregao

rabbit_config = RabbitConfig(fila_entrada='downloads-compra')
consumer = Consumer(Config(rabbit=rabbit_config))
codigo_operacao = 'arquivos_compra'

def callback(message: str) ->  Result[bool, Exception]:
    retorno = Ok(True)
    main_driver = None
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            main_driver = cria_driver(temp_dir)
            dados_pregao = DadosPregao.model_validate_json(message)
            processar_pregao(dados_pregao.codigo_prg, main_driver)
            baixar_e_organizar(dados_pregao, main_driver, temp_dir)
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
