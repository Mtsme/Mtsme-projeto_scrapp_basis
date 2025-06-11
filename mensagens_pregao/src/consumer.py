from datetime import datetime
from typing import Callable

import rabbitpy
from loguru import logger
from result import Ok, Result

from config import Config, RabbitConfig


class Consumer:

    def __init__(self, config: Config):
        rabbit: RabbitConfig = config.rabbit
        self.queue = rabbit.fila_entrada
        self.prefetch_count = rabbit.prefetch_count
        self.dlx = rabbit.exchange_dlx
        self.conn = rabbit.url.__str__()
        self.instance_name = config.instance_name
        logger.debug('Done configuring')

    def consume(self, callback: Callable[[str], Result[bool, Exception]]):
        logger.info(f"Iniciando conexão Rabbit...")
        with rabbitpy.Connection(self.conn) as connection:
            with connection.channel() as channel:
                logger.info("Conectado.")
                queue = rabbitpy.Queue(channel, self.queue, auto_delete=False, durable=True,
                                       dead_letter_exchange=self.dlx, dead_letter_routing_key=self.queue)
                queue.declare()
                try:
                    for message in queue.consume(False, self.prefetch_count):
                        logger.debug('Mensagem recebida.')
                        retorno = callback(message.body)
                        if isinstance(retorno, Ok):
                            message.ack()
                        else:
                            self.publish(self.dlx, self.queue, message.body,
                                         {
                                          "X-Error-Msg": str(retorno.err_value),
                                          "X-Error-Class": type(retorno.err_value).__name__,
                                          "X-Error-Date": datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
                                          "X-Instance-Name": self.instance_name})
                            message.ack()
                except KeyboardInterrupt:
                    logger.warning('Exited consumer!')

    def publish(self, exchange_name, routing_key, msg, headers=None):
        try:
            logger.debug(f"Iniciando conexão Rabbit para publicação na DLQ...")
            with rabbitpy.Connection(self.conn) as connection:
                with connection.channel() as channel:
                    channel.enable_publisher_confirms()
                    properties = None
                    if headers:
                        properties = {"headers": headers}
                    message = rabbitpy.Message(channel, body_value=msg, properties=properties)
                    message.publish(exchange=exchange_name, routing_key=routing_key, mandatory=True)
                    logger.warning(f"Mensagem publicada na DLQ {exchange_name} - routing_key={routing_key}")
            logger.debug(f"Conexão Rabbit encerrada...")
        except Exception as e:
            logger.error(f"Erro RabbitCliente Publish -> {e}...")
            raise e
