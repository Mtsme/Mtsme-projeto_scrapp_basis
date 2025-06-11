from sqlmodel import create_engine, SQLModel

from config import Config
# Importando para criação da tabela
from models import HistoricoMensagem


def migrate_db():
    config: Config = Config()
    engine = create_engine(config.db.url.__str__(),  echo=True)
    SQLModel.metadata.create_all(engine)


if __name__ == '__main__':
    migrate_db()
