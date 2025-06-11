import rabbitpy
from loguru import logger
import json 
from typing import Dict, Any
from decimal import Decimal

class ProducerStatus:
    def __init__(self):
        self.conn = 'amqp://guest:guest@localhost:5672/'
        self.exchange_name = 'dados_propostas'
        self.routing_key = '#'

    def publish_status_update(self, status_data: Dict[str, Any], routing_key: str = None) -> bool:
        """
        Publica uma atualização de status no RabbitMQ.
        """
        routing_key = routing_key or self.routing_key
        
        try:
            # Codificador personalizado para Decimal
            def decimal_encoder(obj):
                if isinstance(obj, Decimal):
                    return str(obj)  # Converte Decimal para string
                raise TypeError(f"Tipo {obj.__class__.__name__} não é serializável em JSON")
            
            with rabbitpy.Connection(self.conn) as connection:
                with connection.channel() as channel:
                    # Declara a exchange
                    exchange = rabbitpy.Exchange(channel, self.exchange_name, durable=True)
                    exchange.declare()
                    
                    # Declara a fila e vincula à exchange
                    queue = rabbitpy.Queue(
                        channel=channel,
                        name=f'{self.exchange_name}.admin',
                        durable=True
                    )
                    queue.declare()
                    queue.bind(self.exchange_name, routing_key)
                    
                    queue2 = rabbitpy.Queue(
                        channel=channel,
                        name=f'{self.exchange_name}.chat-mattermost',
                        durable=True
                    )
                    queue2.declare()
                    queue2.bind(self.exchange_name, routing_key)
                    
                    # Publica a mensagem com o codificador personalizado
                    message = rabbitpy.Message(
                        channel, 
                        json.dumps(status_data, default=decimal_encoder)
                    )
                    message.publish(exchange=self.exchange_name, routing_key=routing_key)
                    
                    return True
                        
        except Exception as e:
            logger.error(f"Erro crítico ao publicar mensagem: {e}")
            return False