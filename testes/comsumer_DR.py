#código que verifica se há mensagens no habbitmq e extrai os dados
#  afim de obter o endereço correto para a url
import json
from pydantic import BaseModel
import rabbitpy
from main_DR import extrair_dr

class EventoPregao(BaseModel):
    codigo_uasg: str
    apelido: str
    id_pregao: int
    codigo_prg: str
    numero_licitacao: str
    id_sistema: int
    acompanhar: bool
   
url_rabbitmq= 'amqp://guest:guest@localhost:5672/'

with rabbitpy.Connection(url_rabbitmq) as connection:
    with connection.channel() as channel:
        queue = rabbitpy.Queue(channel=channel, name='pregao.recursos', auto_delete=False, durable=True)
        for message in queue.consume():
            evento_pregao = EventoPregao.model_validate_json(message.body)
            print(f" Pregão: {evento_pregao.codigo_prg}")
            dados=extrair_dr (evento_pregao,evento_pregao.codigo_prg)
            for item in dados:
                print(item.model_dump_json(indent=2))
            #message.ack() 
