import tempfile 
from loguru import logger 
from result import Result, Ok, Err 
from mensagem_dlq.consumer import Consumer 
from mensagem_dlq.config import inserir_historico, Historico_de_erro 
from comum.models import DadosPregao 
rabbitmq_queue_name = 'historico_mensagem_sessao_publica.comprasnovo.dlq' 
rabbitmq_connection_url = 'amqp://guest:guest@localhost:5672/' 


consumer = Consumer(
    queue_name=rabbitmq_queue_name, 
    connection_url=rabbitmq_connection_url 
)

def callback(message: str, dados_str: str) -> Result[bool, Exception]:
    retorno: Result[bool, Exception] = Ok(True) 
    try:
        try:
            payload_json = DadosPregao.model_validate_json(message) 
        except Exception: 
            payload_json = None 
        
        payload = message 
        dados_historico_model = Historico_de_erro.model_validate_json(dados_str) 
        
        inserir_historico(dados_historico_model, payload, payload_json) 
        
        logger.info("Mensagem processada e histórico inserido com sucesso.")

    except Exception as e:
        retorno = Err(e) 
        logger.exception("Erro ao processar mensagem da DLQ (validação ou inserção no histórico falhou)!")
    finally:
      
        logger.debug(f"Processamento do callback finalizado. Retorno: {type(retorno)}") 
           
    return retorno

def main(): 
    logger.info("Iniciando consumidor de mensagens da DLQ...") 
    consumer.consume(callback)
if __name__ == '__main__':
    main() 