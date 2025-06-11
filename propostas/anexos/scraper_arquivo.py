from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.events import AbstractEventListener
import time
from pydantic import BaseModel
from propostas.anexos.config_arquivo import inserir_dados_pregao, verificar_ultimo_status
from typing import Optional
import json
import os
import re
import io
from datetime import datetime
from minio import Minio
from minio.error import S3Error
from comum.models import DadosPregao
from comum.config import MINIO_CONFIG

def sanitizar_nome_arquivo(nome):
    """Remove caracteres inválidos para nomes de arquivo"""
    nome_sanitizado = re.sub(r'[^\w\-_.]', '_', nome)
    nome_sanitizado = re.sub(r'_+', '_', nome_sanitizado)
    nome_sanitizado = nome_sanitizado.strip('_')
    return nome_sanitizado[:255]

class ArquivoInfo(BaseModel):
    cnpj:str
    nome: str
    data: str
    anexo_minio_url:str
                                                    

class Info_proposta(BaseModel):
    cod_pregao: str
    grupo: str 
    cnpj: str 
    ultimo_arquivo: Optional[str] = None
    lista_arquivo: Optional[list[ArquivoInfo]] = None

def obter_info_anexos(dadospregao:DadosPregao,driver,caminho_download):
    lista_dados = []
    
    try:
        wait = WebDriverWait(driver, timeout=15)
        print(f"Processando Pregao: {dadospregao.codigo_prg}")
        
        # Carrega a página inicial
        driver.get(f"https://cnetmobile.estaleiro.serpro.gov.br/comprasnet-web/public/compras/acompanhamento-compra?compra={dadospregao.codigo_prg}")
        time.sleep(2)
        
        # Espera até que os recursos estejam disponíveis
        div_recursos = wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.width-100'))
        )
        
        for i, div_recurso in enumerate(div_recursos):
            try: 
                if not div_recurso.is_displayed():
                    continue
                    
                # Localiza e clica no botão de recurso
                botoes_recurso = wait.until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'app-botao-icone[class="ng-star-inserted"] button'))
                )
                
                if i >= len(botoes_recurso):
                    continue
                    
                ActionChains(driver).move_to_element(botoes_recurso[i]).click().perform()
                time.sleep(1)
                
                # Processa as propostas
                div_propostas = wait.until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[class="width-100 ng-star-inserted"]'))
                )
                
                for div_proposta in div_propostas:
                    if not div_proposta.is_displayed():
                        continue
                        
                    try:
                        cnpj_element = div_proposta.find_element(By.CSS_SELECTOR, 'div[class="col-md-12 dots"]')
                        dados = Info_proposta(
                            cod_pregao=dadospregao.codigo_prg,
                            grupo=str(i+1),
                            cnpj=cnpj_element.text.strip()
                        )
                        
                        try:
                            botao_expandir = div_proposta.find_element(By.CSS_SELECTOR, 'app-botao-expandir-ocultar button')
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", botao_expandir)
                            ActionChains(driver).move_to_element(botao_expandir).click().perform()
                            time.sleep(1)
                            
                            botoes_anexo = div_proposta.find_elements(By.CSS_SELECTOR, 'button[class="header pt-1 pb-1 align-items-center"]')
                            if len(botoes_anexo) >= 3:
                                try:
                                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", botoes_anexo[2])
                                    ActionChains(driver).move_to_element(botoes_anexo[2]).click().perform()
                                    time.sleep(2)
                                    
                                    data_elementos = div_proposta.find_elements(By.CSS_SELECTOR, 'td[class="text-left pl-1"]')
                                    nome_arquivo = div_proposta.find_elements(By.CSS_SELECTOR, 'td[class="text-left"]')
                                    botoes_download = div_proposta.find_elements(By.CSS_SELECTOR, 'button[class="br-button ml-auto"]')
                                    
                                    if data_elementos and nome_arquivo and len(data_elementos) == len(nome_arquivo):
                                        dados.lista_arquivo = []
                                        for n in range(len(data_elementos)):
                                            try:
                                                data = sanitizar_nome_arquivo(data_elementos[n].text.strip())
                                                nome = sanitizar_nome_arquivo(nome_arquivo[n].text.strip())
        
                                                ultimos = verificar_ultimo_status(
                                                        cod_pregao=dados.cod_pregao,
                                                        grupo=dados.grupo,
                                                        cnpj=dados.cnpj,
                                                        ultimo_arquivo=data
                                                    )
                                                    
                                                if ultimos != data:
                                                    download_result = processar_download(botoes_download[n], dados.cnpj, nome, data, caminho_download, dados.cod_pregao)
                                                    if download_result['success']:
                                                        dados.lista_arquivo.append(ArquivoInfo(
                                                            cnpj=dados.cnpj,
                                                            data=data,
                                                            nome=nome,
                                                            anexo_minio_url=download_result['minio_url']
                                                        ).model_dump())
                                            
                                            except Exception as e:
                                                print(f"Erro ao processar anexo {n}: {e}")
                                        
                                        if data_elementos:
                                            dados.ultimo_arquivo = data_elementos[-1].text.strip()
                                    
                                except Exception as e:
                                    print(f"Erro ao processar anexos: {e}")
                            
                        except Exception as e:
                            print(f"Erro ao expandir proposta: {e}")
                        
                        inserir_dados_pregao(
                            dadospregao.model_dump(),
                            cod_pregao=dados.cod_pregao,
                            grupo=dados.grupo,
                            cnpj=dados.cnpj,
                            ultimo_arquivo=dados.ultimo_arquivo if dados.ultimo_arquivo else 'sem-anexos',
                            lista_anexos=dados.lista_arquivo
                        )
                        lista_dados.append(dados)
                        
                    except Exception as e:
                        print(f"Erro ao processar proposta: {e}")
                
                # Recarrega a página após processar cada recurso
                driver.get(f"https://cnetmobile.estaleiro.serpro.gov.br/comprasnet-web/public/compras/acompanhamento-compra?compra={dadospregao.codigo_prg}")
                time.sleep(2)
                
            except Exception as e:
                print(f'Erro no processamento do recurso {i+1}: {e}')
                # Recarrega a página em caso de erro
                
    
    except Exception as e:
        print(f'Erro geral inesperado: {e}')
    finally:
        if driver:
            driver.quit()
    
    return lista_dados

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
    
    def enviar_arquivo(self, caminho_arquivo, nome_objeto=None):
        """Envia um arquivo para o bucket especificado"""
        try:
            if not nome_objeto:
                nome_objeto = os.path.basename(caminho_arquivo)
            
            # Adiciona timestamp para evitar conflitos
            timestamp = datetime.now()
            nome_base, extensao = os.path.splitext(nome_objeto)
            nome_unico = f"{nome_base}_{timestamp}{extensao}"
            
            # Faz o upload do arquivo
            self.client.fput_object(
                self.bucket_padrao,
                nome_unico,
                caminho_arquivo
            )
            

            # Retorna a URL do arquivo
            return f"{self.bucket_padrao}/{nome_unico}"
        
        except S3Error as e:
            print(f"Erro ao enviar arquivo {caminho_arquivo} para o bucket {self.bucket_padrao}: {e}")
            return None

# Modifique a função processar_download para usar o bucket específico
def processar_download(botao, cnpj, prefixo, identificador, caminho_download, cod_pregao):
    max_tentativas = 3
    tentativa = 0
    download_ok = False
    arquivo_baixado = None
    url_minio = None
    
    minio_client = MinIOClient(MINIO_CONFIG)

    while tentativa < max_tentativas and not download_ok:
        try:
            # 1. Lista arquivos antes do download
            arquivos_antes = set(os.listdir(caminho_download))
            
            # 2. Clica no botão de download
            botao.click()
            
            # 3. Aguarda o download completar (timeout de 15 segundos)
            tempo_espera = 0
            while tempo_espera < 15:
                arquivos_depois = set(os.listdir(caminho_download))
                novos_arquivos = arquivos_depois - arquivos_antes
                
                if novos_arquivos:
                    arquivo_baixado = max(
                        [os.path.join(caminho_download, f) for f in novos_arquivos],
                        key=os.path.getctime
                    )
                    
                    if os.path.exists(arquivo_baixado):
                        try:
                            with open(arquivo_baixado, 'rb') as f:
                                pass
                            
                            if os.path.getsize(arquivo_baixado) > 0:
                                download_ok = True
                                break
                            else:
                                os.remove(arquivo_baixado)
                                arquivo_baixado = None
                        except IOError:
                            pass
                
                time.sleep(1)
                tempo_espera += 1
            
            if not download_ok:
                tentativa += 1
                time.sleep(1)
                
        except Exception as e:
            print(f"Erro durante o download (tentativa {tentativa+1}): {e}")
            tentativa += 1
            time.sleep(1)
    
    if download_ok and arquivo_baixado:
        try:
            extensao = os.path.splitext(arquivo_baixado)[1]
            cnpj_limpo = sanitizar_nome_arquivo(cnpj)
            prefixo_limpo = sanitizar_nome_arquivo(prefixo)
            id_limpo = sanitizar_nome_arquivo(identificador)
            
            nome_arquivo_limpo = f"cnpj-{cnpj_limpo}_{prefixo_limpo}_Data_{id_limpo}{extensao}"
            novo_nome = os.path.join(caminho_download, nome_arquivo_limpo)
            
            # Evita sobrescrever arquivos existentes
            contador = 1
            nome_base = novo_nome
            while os.path.exists(novo_nome):
                nome, ext = os.path.splitext(nome_base)
                novo_nome = f"{nome}_{contador}{ext}"
                contador += 1
            
            os.rename(arquivo_baixado, novo_nome)
            print(f'Download concluído e renomeado para: {os.path.basename(novo_nome)}')
            
            # Cria/verifica bucket específico para o pregão
            pregao=sanitizar_nome_arquivo(cod_pregao)
            caminho_arquivo = f'{pregao}/propostas/{nome_arquivo_limpo}'.lower()  # MinIO requer buckets em lowercase
           
            # Faz upload para o bucket específico
            url_minio = minio_client.enviar_arquivo(novo_nome, caminho_arquivo)
            if url_minio:
                print(f'Arquivo enviado para MinIO (bucket {caminho_arquivo}): {url_minio}')
            
            return {'success': True, 'local_path': novo_nome, 'minio_url': url_minio}
        
        except Exception as e:
            print(f"Erro ao processar arquivo {arquivo_baixado}: {e}")
            return {'success': False, 'error': str(e)}
    
    print(f"Falha ao baixar {prefixo}_{identificador} após {max_tentativas} tentativas")
    return {'success': False, 'error': 'Número máximo de tentativas excedido'}

