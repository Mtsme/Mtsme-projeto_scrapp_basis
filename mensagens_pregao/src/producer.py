import rabbitpy

from config import Config
from loguru import logger


class Producer:

    def __init__(self, config: Config):
        rabbit = config.rabbit
        self.conn = (rabbit.url.__str__())
        self.exchange = rabbit.exchange_mensagens

    def publish(self, message, routing_key=''):
        with rabbitpy.Connection(self.conn) as connection:
            with connection.channel() as channel:
                channel.enable_publisher_confirms()
                message = rabbitpy.Message(channel, message)
                is_publish_successful = message.publish(exchange=self.exchange, routing_key=routing_key,
                                                        mandatory=True)
                if is_publish_successful:
                    logger.debug(f'Mensagem publicada no exchange: {self.exchange}')
                else:
                    logger.error(f'Publicação no exchange: {self.exchange} falhou!')
