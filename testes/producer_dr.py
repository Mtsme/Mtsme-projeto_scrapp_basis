import rabbitpy
from loguru import logger
import json 
from typing import Dict, Any
from datetime import datetime
import time

class ProducerDR:
    def __init__(self):
        self.conn = 'amqp://guest:guest@localhost:5672/'
        self.exchange_name = 'recursos.decisao.revisao'
        self.routing_key = '#'

    def publish_status_update(self, status_data: Dict[str, Any], routing_key: str = None) -> bool:
        """
        Publica uma atualização de status no RabbitMQ.
        """
        routing_key = routing_key or self.routing_key
        
        try:
            with rabbitpy.Connection(self.conn) as connection:
                with connection.channel() as channel:
                    # Declara exchange
                    exchange = rabbitpy.Exchange(channel, self.exchange_name,exchange_type='topic', durable=True)
                    exchange.declare()
                    
                    # Declara fila e vincula à exchange
                    queue = rabbitpy.Queue(
                        channel=channel,
                        name=f'{self.exchange_name}.queue',
                        durable=True
                    )
                    queue.declare()
                    queue.bind(self.exchange_name, routing_key)
                    
                    # Publica a mensagem
                    message = rabbitpy.Message(channel, json.dumps(status_data,default=str))
                    message.publish(exchange=self.exchange_name, routing_key=routing_key)
                    
                    return True
                        
        except Exception as e:
            logger.error(f"Erro crítico ao publicar mensagem: {e}")
            return False

class ProducerDLX:
    def __init__(self):
        self.conn = 'amqp://guest:guest@localhost:5672/'
        self.exchange_name = 'DLX'
        self.routing_key = 'historico_mensagem_sessao_publica.comprasnovo'

    def publish_dlx_update(self, status_data: Dict[str, Any], routing_key: str = None) -> bool:
        """
        Publica uma atualização de erro no RabbitMQ.
        """
        routing_key = routing_key or self.routing_key
        
        try:
            with rabbitpy.Connection(self.conn) as connection:
                with connection.channel() as channel:
                    # Declara exchange
                    exchange = rabbitpy.Exchange(channel, self.exchange_name,exchange_type='topic', durable=True)
                    exchange.declare()
                    
                    # Declara fila e vincula à exchange
                    queue = rabbitpy.Queue(
                        channel=channel,
                        name='historico_mensagem_sessao_publica.comprasnovo',
                        durable=True
                    )
                    queue.declare()
                    queue.bind(self.exchange_name, routing_key)
                    
                    # Publica a mensagem
                    message = rabbitpy.Message(channel, json.dumps(status_data,default=str))
                    message.publish(exchange=self.exchange_name, routing_key=routing_key)
                    
                    return True
                        
        except Exception as e:
            logger.error(f"Erro crítico ao publicar mensagem: {e}")
            return False