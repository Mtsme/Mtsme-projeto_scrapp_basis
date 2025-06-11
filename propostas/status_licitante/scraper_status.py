from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (TimeoutException, NoSuchElementException, ElementClickInterceptedException)
from selenium.webdriver.common.action_chains import ActionChains
import time
from pydantic import BaseModel
from propostas.status_licitante.config_status import inserir_status_pregao
from typing import Optional
import logging
from loguru import logger
from comum.models import DadosPregao

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def inicio(get,driver):
    driver.get("https://cnetmobile.estaleiro.serpro.gov.br/comprasnet-web/public/compras/acompanhamento-compra?compra=" + str(get))

def obter_status_anexos(dadosprg: DadosPregao,driver):
    lista_dados = []

    class Info_status(BaseModel):
        cod_pregao: str
        grupo: str 
        cnpj: str 
        status: Optional[str] = None 
        motivo : Optional[str] = None 

    inicio(dadosprg.codigo_prg,driver) 
    wait = WebDriverWait(driver, timeout=10)  # Aumentado para 10 segundos
    
    print(f"Processando Pregao: {dadosprg.codigo_prg}")
    
    try:
        div_recursos = wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.width-100'))
        )
        num = len(div_recursos)
            
        for i in range(num):
            j = i + 1
            try: 
                div_recursos = wait.until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.width-100')))
                div_recurso = div_recursos[i]

                if div_recurso.is_displayed():
                    try:
                        botoes_recurso = wait.until(
                            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'app-botao-icone[class="ng-star-inserted"] button'))
                        )
                        if i < len(botoes_recurso):
                            # Usando ActionChains para clicar de forma mais confiável
                            ActionChains(driver).move_to_element(botoes_recurso[i]).pause(1).click().perform()
                            time.sleep(1)  # Aumentado tempo de espera após clique
                
                            try:
                                div_propostas = wait.until(
                                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[class="width-100 ng-star-inserted"]'))
                                )
                                
                                for div_proposta in div_propostas:
                                    if div_proposta.is_displayed:
                                        try:
                                            cnpj_element = div_proposta.find_element(By.CSS_SELECTOR, 'div[class="col-md-12 dots"]')
                                            dados = Info_status(
                                                cod_pregao=dadosprg.codigo_prg,
                                                grupo=str(j),
                                                cnpj=cnpj_element.text.strip() )
                                            
                                            
                                            try:
                                                status_element = div_proposta.find_element(By.CSS_SELECTOR, 'div[class="p-element color-support-03 situacao pr-1 ng-star-inserted"]')
                                                dados.status=status_element.text.strip()
                                            except: None
                                           
                                            
                                            try:
                                                botao_expandir = div_proposta.find_element(By.CSS_SELECTOR, 'app-botao-expandir-ocultar button')
                                                # Solução para botão não clicável
                                                try:
                                                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", botao_expandir)
                                                    time.sleep(1)
                                                    ActionChains(driver).move_to_element(botao_expandir).pause(1).click().perform()
                                                    time.sleep(1)  # Aumentado tempo de espera
                                                    
                                                    # Clica para expandir anexos
                                                    try:
                                                        botoes_anexo = div_proposta.find_elements(By.CSS_SELECTOR, 'button[class="header pt-1 pb-1 align-items-center"]')
                                                        # Solução para índice fora de range
                                                        if len(botoes_anexo) >= 3:
                                                            try:
                                                                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", botoes_anexo[1])
                                                                time.sleep(1)
                                                                ActionChains(driver).move_to_element(botoes_anexo[1]).pause(1).click().perform()
                                                                time.sleep(1)  # Aumentado tempo de espera
                                                                
                                                                # Obter data do arquivo
                                                                try:
                                                                    div_motivo= div_proposta.find_element(By.CSS_SELECTOR, 'div[class="col-md-12 col-sm-12 col-12 pt-2 ng-star-inserted"]')
                                                                                
                                                                    motivo_elemento = div_motivo.find_element(By.CSS_SELECTOR, 'div[class="cp-valor-item-08"]')
                                                                    
                                                                    dados.motivo = motivo_elemento.text.strip()
                                                                    
                                                                    
                                                                except NoSuchElementException:
                                                                    print(f"Não encontrou elementos de motivo para o CNPJ: {dados.cnpj}")
                                                        
                                                                except Exception as e:
                                                                    print(f"Erro inesperado ao obter motivo do arquivo: {e}")
                                                            except ElementClickInterceptedException:
                                                                print(f"Botão de propostas não clicável para o CNPJ: {dados.cnpj}. Tentando novamente...")
                                                                # Segunda tentativa com JavaScript
                                                                try:
                                                                    driver.execute_script("arguments[0].click();", botoes_anexo[1])
                                                                    time.sleep(1)
                                                                except Exception as e:
                                                                    print(f"Falha ao clicar via JavaScript: {e}")
                                                            except Exception as e:
                                                                print(f"Erro ao clicar no botão de propostas: {e}")
                                                        else:
                                                            print(f"Apenas {len(botoes_anexo)} botões de propostas encontrados para CNPJ: {dados.cnpj}")
                                                    except NoSuchElementException:
                                                        print(f"Não encontrou botões de propostas para o CNPJ: {dados.cnpj}")
                                                    except Exception as e:
                                                        print(f"Erro inesperado ao expandir propostas do cnpj: {dados.cnpj}, {e}")
                                                
                                                except NoSuchElementException:
                                                    print(f"Botão expandir não encontrado para proposta {j}")
                                                except Exception as e:
                                                    print(f"Erro ao expandir proposta {j}: {e}")
                                            
                                            except NoSuchElementException:
                                                print(f"Botão expandir não encontrado para proposta {j}")
                                            except Exception as e:
                                                print(f"Erro inesperado ao expandir proposta: {e}")
                                            
                                            inserir_status_pregao(
                                                dadospregao=dadosprg.model_dump(),
                                                cod_pregao=dados.cod_pregao,
                                                grupo=dados.grupo,
                                                cnpj=dados.cnpj,
                                                status=dados.status,
                                                motivo=dados.motivo)
                                            
                                                   
                                            lista_dados.append(dados)

                                        except NoSuchElementException:
                                            print(f"Elementos da proposta não encontrados para recurso {j}")
                                        except Exception as e:
                                            print(f"Erro inesperado ao processar proposta: {e}")
                                
                                
                            except TimeoutException:
                                print(f"Timeout ao encontrar div de propostas para recurso {j}")
                            except Exception as e:
                                print(f"Erro inesperado ao encontrar div de propostas: {e}")
                    
                    except TimeoutException:
                        print(f"Timeout ao encontrar botões de recurso para índice {i}")
                    except Exception as e:
                        print(f"Erro inesperado com botões de recurso: {e}")
                
                # Recarregar a página para o próximo recurso
                driver.get("https://cnetmobile.estaleiro.serpro.gov.br/comprasnet-web/public/compras/acompanhamento-compra?compra=" + str(dadosprg.codigo_prg))
                time.sleep(2)  # Aumentado tempo de espera após recarregar
                
            except Exception as e:
                print(f'Erro no processamento da proposta {i}: {e}')
    
    except TimeoutException:
        print('Timeout ao carregar elementos principais da página')
    except Exception as e:
        print(f'Erro geral inesperado: {e}')
    finally:
        driver.quit()
    
    return lista_dados