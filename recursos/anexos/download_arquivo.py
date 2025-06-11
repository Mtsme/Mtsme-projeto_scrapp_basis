# download_arquivo.py
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import re
from selenium.common.exceptions import TimeoutException
from recursos.anexos.abre_e_clica import interagir_com_abas, inicio
import time
from pydantic import BaseModel
from recursos.anexos.config_downloads import inserir_dados_pregao, verificar_ultimo_status
import json
from minio import Minio
from minio.error import S3Error
from comum.models import DadosPregao
from comum.config import MINIO_CONFIG



def sanitizar_nome_arquivo(nome):
    """Remove caracteres inválidos para nomes de arquivo"""# Remove caracteres especiais, mantendo apenas letras, números, hífen e underline
    nome_sanitizado = re.sub(r'[^\w\-_.]', '_', nome)# Remove múltiplos underlines consecutivos
    nome_sanitizado = re.sub(r'_+', '_', nome_sanitizado)# Remove underlines no início e no fim
    nome_sanitizado = nome_sanitizado.strip('_')# Limita o tamanho do nome (255 caracteres é o limite comum em sistemas de arquivos)
    return nome_sanitizado[:255]

class Infoanexo(BaseModel):
    cod_prg:str
    grupo:str
    secao:str
    cnpj:str

def baixar_arquivos(driver,dadosprg:DadosPregao,download_path):
    print(f"Processando compra: {dadosprg.codigo_prg}")
    
    inicio(dadosprg.codigo_prg,driver)
    wait = WebDriverWait(driver, timeout=6)
    
    try:
        div_recursos = wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.width-100'))
        )
        num = len(div_recursos)
        
        for i in range(num):
            try: 
                div_recursos = wait.until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.width-100')))
                div_recurso = div_recursos[i]

                if div_recurso.is_displayed():
                    botoes_recurso = wait.until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'app-botao-icone[class="ng-star-inserted"] button'))
                    )
                    if i < len(botoes_recurso):
                        botoes_recurso[i].click()
                        time.sleep(2)

                    interagir_com_abas(driver)
                    
                    try:
                        elemento = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, '.p-dropdown-trigger-icon'))
                        )
                        elemento.click()
                        time.sleep(1)

                        qtd_botoes = wait.until(
                            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'p-dropdownitem.p-element'))
                        ) 
                        time.sleep(1)
                        num = len(qtd_botoes)
                        elemento.click()
                    except TimeoutException:
                        print("Erro ao trocar de seção.")
                        num = 1

                    for j in range(num):
                        try:
                            elemento = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, '.p-dropdown-trigger-icon'))
                            )
                            elemento.click()
                            time.sleep(1)
                            troca_sessao = wait.until(
                                    EC.element_to_be_clickable((By.CSS_SELECTOR, f'p-dropdownitem.p-element:nth-child({j+1})')))
                            troca_sessao.click()
                        except Exception as e:
                            print(f"Erro ao trocar sessão: {e}")

                        try:
                            div_downloads = wait.until(
                                EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[class="row cp-itens-card cp-item-expansivel p-1 justify-content-between"]'))
                            )
                            
                            for div_recurso in div_downloads:
                                if div_recurso.is_displayed():
                                    try:
                                        botao_expandir = div_recurso.find_element(By.CSS_SELECTOR, 'app-botao-expandir-ocultar button')
                                        botao_expandir.click()
                                        time.sleep(3)
                                        cnpj1 = div_recurso.find_element(By.CSS_SELECTOR, 'div.cp-item-bold').text.strip()
                                        cnpj = sanitizar_nome_arquivo(cnpj1)
                                      
                                        dados=Infoanexo(
                                            cod_prg=dadosprg.codigo_prg,
                                            grupo=str(i+1),
                                            secao=str(j+1),
                                            cnpj=cnpj
                                        )

                                        # Processar o primeiro tipo de botões de download
                                        try:
                                            botoes_download = div_recurso.find_elements(By.CSS_SELECTOR, 'button[class="br-button ml-auto"]')
                                            botao=botoes_download[0]

                                            if botao:
                                                ultimo=verificar_ultimo_status(
                                                cod_pregao=dados.cod_prg,
                                                grupo=dados.grupo,
                                                cnpj=dados.cnpj,
                                                tipo="recurso",
                                                arquivos=cnpj
                                            )
                                                arquivos1 = None
                                                if ultimo != "recurso":
                                                    arquivo1=processar_download(botao, cnpj, "recurso", download_path,dadosprg.codigo_prg)
                                                    if arquivo1['success']:
                                                        arquivos1=arquivo1['minio_url']
                                                inserir_dados_pregao(
                                                    dadospregao=dadosprg.model_dump(),
                                                    cod_pregao=dados.cod_prg,
                                                    grupo=dados.grupo,
                                                    cnpj=dados.cnpj,
                                                    tipo="recurso",
                                                    arquivos=cnpj,
                                                    localarquivos=json.dumps(arquivos1) if arquivos1 else None
                                                )

                                               
                                            
                                        except Exception as e:
                                            print(f"Erro de download do cnpj:{cnpj,e}")

                                        # Processar o segundo tipo de botões de download
                                        try:
                                            botoes_download2 = div_recurso.find_elements(By.CSS_SELECTOR, 'button[class="br-button ml-auto"]')
                                            cnpje2 = div_recurso.find_element(By.CSS_SELECTOR, 'td.col-2').text.strip()
                                            cnpj2 = sanitizar_nome_arquivo(cnpje2)
                                            if len(botoes_download2)>1:
                                                botao2=botoes_download2[-1]
                                                if botao2:
                                                     ultimo=verificar_ultimo_status(
                                                            cod_pregao=dados.cod_prg,
                                                            grupo=dados.grupo,
                                                            cnpj=dados.cnpj,
                                                            tipo="contrarrazao",
                                                            arquivos=cnpj2
                                                        )
                                                arquivos2 = None
                                                if ultimo != "contrarrazao":
                                                    arquivo2=processar_download(botao2, cnpj, "contrarrazao", download_path,dadosprg.codigo_prg)
                                                    if arquivo2['success']:
                                                        arquivos2=arquivo2['minio_url']
                                                inserir_dados_pregao(
                                                    dadospregao=dadosprg.model_dump(),
                                                    cod_pregao=dados.cod_prg,
                                                    grupo=dados.grupo,
                                                    cnpj=dados.cnpj,
                                                    tipo="contrarrazao",
                                                    arquivos=cnpj2,
                                                    localarquivos= arquivos2 if arquivos2 else None
                                                )
                                        except Exception as e:
                                            print(f"Erro de download do cnpj:{cnpj2,e}")
                                        
                                    
                                    except Exception as e:
                                        print(f"Erro ao expandir recurso: {e}")
                                    
                                else:
                                    print("Div de recurso não está visível")
                        except: None
                driver.get("https://cnetmobile.estaleiro.serpro.gov.br/comprasnet-web/public/compras/acompanhamento-compra?compra="+str(dadosprg.codigo_prg))
            except Exception as e:
                print(f'Erro no processamento do recurso {i}: {e}')
                
            

    except Exception as e:
        print(f'Erro geral em downloads: {e}')

# Primeiro, modifique a classe MinIOClient para aceitar nomes dinâmicos de buckets
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
    
        

    def verificar_ou_criar_bucket(self, nome_bucket):
        """Verifica se o bucket existe, se não, cria um novo"""
        try:
            if not self.client.bucket_exists(nome_bucket):
                self.client.make_bucket(nome_bucket)
                print(f"Bucket '{nome_bucket}' criado com sucesso")
            return True
        except S3Error as e:
            print(f"Erro ao verificar/criar o bucket {nome_bucket}: {e}")
            return False
    
    # Modificar o método enviar_arquivo na classe MinIOClient:
    def enviar_arquivo(self, download_path, nome_objeto=None):
        """Envia um arquivo para o bucket especificado"""
        try:
            if not nome_objeto:
                nome_objeto = os.path.basename(download_path)
            
            # Faz o upload do arquivo com o nome_objeto completo (incluindo caminho)
            self.client.fput_object(
                self.bucket_padrao,
                nome_objeto,  # Usa o nome_objeto completo que inclui o caminho
                download_path
            )

            # Retorna o caminho completo no MinIO
            return f"{self.bucket_padrao}/{nome_objeto}"
        
        except S3Error as e:
            print(f"Erro ao enviar arquivo {download_path} para o bucket {self.bucket_padrao}: {e}")
            return None

# Modifique a função processar_download para usar o bucket específico
def processar_download(botao, cnpj, identificador, caminho_download, cod_pregao):
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
            id_limpo = sanitizar_nome_arquivo(identificador)
            
            nome_arquivo_limpo = f"cnpj-{cnpj_limpo}{id_limpo}{extensao}"
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
            codprg=sanitizar_nome_arquivo(cod_pregao)
            
            # Define o caminho no MinIO
            object_name = f"{codprg}/recursos/{nome_arquivo_limpo}".lower()
            
            # Faz upload para o MinIO
            url_minio = minio_client.enviar_arquivo(novo_nome, object_name)
            if url_minio:
                print(f'Arquivo enviado para MinIO: {url_minio}')
            
            return {'success': True, 'local_path': novo_nome, 'minio_url': url_minio}
            

        
        except Exception as e:
            print(f"Erro ao processar arquivo {arquivo_baixado}: {e}")
            return {'success': False, 'error': str(e)}
    
    print(f"Falha ao baixar {identificador} após {max_tentativas} tentativas")
    return {'success': False, 'error': 'Número máximo de tentativas excedido'}





