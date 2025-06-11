import os
from typing import Tuple, Type

from pydantic import PostgresDsn, AmqpDsn, BaseModel
from pydantic_core import Url, MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict, PydanticBaseSettingsSource, YamlConfigSettingsSource

YAML_CONFIG_FILE = os.environ.get('YAML_CONFIG_FILE', 'config.yaml')

MINIO_CONFIG = {
    'endpoint': 'localhost:9000',
    'access_key': 'miniobasis',
    'secret_key': 'miniobasis',
    'secure': False,  # True para HTTPS, False para HTTP
    'bucket_name': 'licitacao'
}
DB_CONFIG = {
    'dbname': 'scraper',
    'user': 'scraper',
    'password': 'scraper',
    'host': 'localhost',
    'port': 5432
}

class RabbitConfig(BaseModel):
    url: AmqpDsn = Url('amqp://guest:guest@localhost:5672/%2F')
    prefetch_count: int = 1
    fila_entrada: str = 'filaentrada'
    exchange_saida: str = 'exchangesaida'
    exchange_dlx: str = 'DLX'
    routing_dlq: str = 'historico_mensagem_sessao_publica_comprasnovo'
    


class DbConfig(BaseModel):
    url: PostgresDsn = MultiHostUrl('postgresql+psycopg2://scraper:scraper@localhost:5432/scraper')
    max_connections: int = 5


class Config(BaseSettings):
    model_config = SettingsConfigDict(yaml_file=YAML_CONFIG_FILE, extra='ignore', env_nested_delimiter='__')
    rabbit: RabbitConfig = RabbitConfig()
    db: DbConfig = DbConfig()
    default_log_level: str = 'INFO'
    instance_name: str = 'primary'

    @classmethod
    def settings_customise_sources(
            cls,
            settings_cls: Type[BaseSettings],
            init_settings: PydanticBaseSettingsSource,
            env_settings: PydanticBaseSettingsSource,
            dotenv_settings: PydanticBaseSettingsSource,
            file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            YamlConfigSettingsSource(settings_cls),
            file_secret_settings
        )
