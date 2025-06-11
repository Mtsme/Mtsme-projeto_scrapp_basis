import json
import os
import time
from datetime import datetime

from loguru import logger
from minio import Minio
from minio.error import S3Error

from comum.models import DadosPregao
from downloads_compra.config import inserir_dados_pregao, verificar_ultimo_status
from downloads_compra.download_compra import processar_downloads
from comum.config import MINIO_CONFIG

def mover_para_diretorio_final(dadosprg, origem_temp: str, codigo_prg: str):

    anexos = []
    
    minio_client = MinIOClient(MINIO_CONFIG)
    locais=[]

    for nome in os.listdir(origem_temp):
        origem = os.path.join(origem_temp, nome)
        caminho_arquivo = f'{codigo_prg}/anexos.gerais/{nome}'.lower()
        anexos.append(nome)
        caminho=minio_client.enviar_arquivo(origem, caminho_arquivo)
        locais.append(caminho)

    ultimo = verificar_ultimo_status(cod_pregao=codigo_prg)

    if ultimo != anexos:
        inserir_dados_pregao(
            dadospregao=dadosprg,
            cod_pregao=codigo_prg,
            anexos=json.dumps(anexos),
            url_anexos=locais
        )

class MinIOClient:
    def __init__(self, config):
        self.client = Minio(
            config['endpoint'],
            access_key=config['access_key'],
            secret_key=config['secret_key'],
            secure=config['secure']
        )
        self.bucket_padrao = config['bucket_name']  # Bucket padrão (não será mais usado como principal)
        self.verificar_ou_criar_bucket(self.bucket_padrao)

    # Esta linha deve estar no seu código, após a definição da classe MinIOClient

    def verificar_ou_criar_bucket(self, nome_bucket) -> None:
        """Verifica se o bucket existe, se não, cria um novo"""
        try:
            if not self.client.bucket_exists(nome_bucket):
                self.client.make_bucket(nome_bucket)
                print(f"Bucket '{nome_bucket}' criado com sucesso")
            return True
        except S3Error as e:
            print(f"Erro ao verificar/criar o bucket {nome_bucket}: {e}")
            return False

    def enviar_arquivo(self, caminho_arquivo, nome_objeto=None) -> str:
        """Envia um arquivo para o bucket especificado"""
        logger.debug(f"Enviando: {caminho_arquivo}")
        try:
            if not nome_objeto:
                nome_objeto = os.path.basename(caminho_arquivo)

            # Verifica se o arquivo existe
            if not os.path.exists(caminho_arquivo):
                print(f"Arquivo {caminho_arquivo} não encontrado")
                return None

            # Adiciona timestamp para evitar conflitos
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_base, extensao = os.path.splitext(nome_objeto)
            nome_unico = f"{nome_base}_{timestamp}{extensao}"

            # Faz o upload do arquivo
            self.client.fput_object(
                self.bucket_padrao,
                nome_unico,
                caminho_arquivo
            )
            logger.debug(f"Caminho Minio: {self.bucket_padrao}/{nome_unico}")
            # Retorna a URL do arquivo
            return f"{self.bucket_padrao}/{nome_unico}"

        except S3Error as e:
            logger.error(f"Erro ao enviar arquivo {caminho_arquivo} para o bucket {self.bucket_padrao}: {e}")
            return None
        except Exception as e:
            logger.error(f"Erro inesperado ao enviar arquivo: {e}")
            return None


def baixar_e_organizar(dadosprg: DadosPregao, driver, temp_dir):
    logger.debug(f"Pasta temporária criada: {temp_dir}")
    url = f"https://cnetmobile.estaleiro.serpro.gov.br/comprasnet-web/public/compras/acompanhamento-compra?compra={dadosprg.codigo_prg}"
    driver.get(url)
    time.sleep(5)
    sucesso = processar_downloads(driver, temp_dir, dadosprg.codigo_prg)
    logger.debug("\nArquivos baixados:")
    for nome in os.listdir(temp_dir):
        logger.debug(f"- {nome}")
    mover_para_diretorio_final(dadosprg, temp_dir, dadosprg.codigo_prg)
    if sucesso:
        logger.debug("Downloads concluídos com sucesso!")
    else:
        logger.warning("Alguns downloads falharam.")
