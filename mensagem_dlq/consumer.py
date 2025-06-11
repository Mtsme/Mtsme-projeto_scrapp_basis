from typing import Callable
import json

import rabbitpy 
import rabbitpy.exceptions as rpy_exc 
from loguru import logger
from result import Ok, Result

# Função auxiliar para decodificar valores se forem bytes
def decode_if_bytes(value, encoding='utf-8', errors='replace'):
    if isinstance(value, bytes):
        return value.decode(encoding, errors=errors)
    return value

class Consumer:

    def __init__(self, queue_name: str, connection_url: str, prefetch_count: int = 1):
        self.queue = queue_name
        self.prefetch_count = prefetch_count
        self.conn = connection_url
        logger.debug(f"Consumer inicializado para consumir da fila '{self.queue}' na conexão '{self.conn}' (sem declaração de fila).")

    def consume(self, callback: Callable[[str, str], Result[bool, Exception]]):
        logger.info(f"Tentando conectar ao RabbitMQ em {self.conn}...")
        try:
            with rabbitpy.Connection(self.conn) as connection:
                logger.info("Conexão com RabbitMQ estabelecida.")
                with connection.channel() as channel:
                    logger.info("Canal RabbitMQ aberto.")
                    
                    queue_instance = rabbitpy.Queue(channel, name=self.queue)
                    
                    logger.info(f"Iniciando consumo de mensagens da fila '{self.queue}'...")
                    for message in queue_instance.consume(prefetch=self.prefetch_count):
                        logger.debug(f"Mensagem recebida da fila '{self.queue}'. ID de Entrega: {message.delivery_tag}")
                        
                        headers_from_message = message.properties.get('headers') if message.properties else {}
                        message_body_str = message.body.decode('utf-8', errors='replace')
                        
                        # Decodifica os valores dos cabeçalhos se forem bytes
                        error_headers = {
                            "x_error_msg": decode_if_bytes(headers_from_message.get("X-Error-Msg")),
                            "x_error_class": decode_if_bytes(headers_from_message.get("X-Error-Class")),
                            "x_error_date": decode_if_bytes(headers_from_message.get("X-Error-Date")), 
                            "x_instance_name": decode_if_bytes(headers_from_message.get("X-Instance-Name")),
                            "x_source_queue": decode_if_bytes(headers_from_message.get("X-Source-Queue")),
                            "payload": message_body_str 
                        }
                        
                        # error_headers serializável em JSON e compatível com o modelo
                        error_headers_json = json.dumps(error_headers)
                        retorno = callback(message_body_str, error_headers_json)
                        
                        if isinstance(retorno, Ok):
                            message.ack()
                            logger.info(f"Mensagem {message.delivery_tag} processada com sucesso e ACK enviada.")
                        else:
                            error_details = retorno.err() if retorno.is_err() else "Erro desconhecido no callback"
                            logger.error(f"Falha no processamento da mensagem {message.delivery_tag}. Erro: {error_details}. Enviando NACK (requeue=False).")
                            message.nack(requeue=False)

        except rpy_exc.AMQPException as e_amqp_outer: 
            logger.error(f"FALHA AMQP (possivelmente de conexão) ao tentar conectar/configurar o RabbitMQ em '{self.conn}'. "
                         f"Tipo: {type(e_amqp_outer).__name__}, Detalhes: {e_amqp_outer}. "
                         f"Verifique as configurações de conexão e o status do servidor RabbitMQ.", exc_info=True)
        except Exception as e_main_setup:
            logger.exception(f"Ocorreu um erro geral na configuração do consumidor ou na tentativa de conexão inicial: {e_main_setup}")