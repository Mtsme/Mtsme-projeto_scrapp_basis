import os
import random
import time

from retry import retry
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from downloads_compra.config import ESPERA_FIXA_PAGINACAO

MAX_TENTATIVAS = 5  # Número máximo de tentativas por item

def espera_aleatoria(min=3, max=15):
    time.sleep(random.uniform(min, max))

def verificar_arquivo_baixado(temp_dir, padroes):
    """Verifica se algum arquivo na pasta corresponde aos padrões esperados"""
    for arquivo in os.listdir(temp_dir):
        for padrao in padroes:
            if padrao in arquivo:
                return arquivo
    return None

def nomes_padrao(codigo, item_nome):
    """Gera os padrões de nome de arquivo esperados para cada tipo de item"""
    if "Edital" in item_nome:
        return [f"{codigo}.zip", f"{codigo}"]
    elif "Todos os relatórios" in item_nome or "relatórios e termos" in item_nome:
        return [f"relatorios-compra-{codigo}.zip", f"relatorios-compra-{codigo}"]
    elif "Termos e Relatório" in item_nome or "Relatório das declarações" in item_nome:
        return [f"relatorio-termo-aceite-{codigo}.pdf", f"relatorio-termo-aceite-{codigo}"]
    return [f"{codigo}"]

@retry(exceptions=Exception, tries=MAX_TENTATIVAS, delay=2, backoff=10)
def tentar_download(driver, item_nome, temp_dir, codigo_prg, tentativa):
    """Tenta fazer o download com recarregamento da página a cada tentativa"""
    try:
        if tentativa > 1:
            url = f"https://cnetmobile.estaleiro.serpro.gov.br/comprasnet-web/public/compras/acompanhamento-compra?compra={codigo_prg}"
            driver.get(url)
            time.sleep(5)
        
        padroes = nomes_padrao(codigo_prg, item_nome)
        arquivo_existente = verificar_arquivo_baixado(temp_dir, padroes)
        
        if arquivo_existente:
            print(f"[SUCESSO - Tentativa {tentativa}] Arquivo já baixado: {arquivo_existente}")
            return True
        
        if not abrir_lista_downloads(driver):
            raise Exception("Falha ao abrir menu de downloads")
        
        itens_menu = obter_itens_menu(driver)
        item_encontrado = None
        for item, nome in itens_menu:
            if nome == item_nome:
                item_encontrado = item
                break
                
        if not item_encontrado:
            raise Exception(f"Item '{item_nome}' não encontrado no menu")
            
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", item_encontrado)
        time.sleep(0.5)
        ActionChains(driver).move_to_element(item_encontrado).pause(0.3).click().perform()
        print(f"[AGUARDANDO - Tentativa {tentativa}] Tentando baixar: {item_nome}")
        
        tempo_decorrido = 0
        while tempo_decorrido < ESPERA_FIXA_PAGINACAO:
            arquivo = verificar_arquivo_baixado(temp_dir, padroes)
            if arquivo:
                print(f"[SUCESSO - Tentativa {tentativa}] Download concluído: {arquivo}")
                return True
            time.sleep(1)
            tempo_decorrido += 1
            
        raise Exception("Nenhum arquivo correspondente encontrado")
        
    except Exception as e:
        print(f"[ERRO - Tentativa {tentativa}] Falha no item '{item_nome}': {str(e)[:200]}")
        raise

def abrir_lista_downloads(driver):
    try:
        css_selector = 'button.br-button.ml-auto.secondary i.fa-download.fas'
        botoes = WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, css_selector)))
        
        if not botoes:
            return False
            
        ultimo_botao = botoes[-1]
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", ultimo_botao)
        time.sleep(0.5)
        ActionChains(driver).move_to_element(ultimo_botao).pause(0.3).click().perform()
        time.sleep(1)
        return True
        
    except Exception as e:
        print(f"Erro ao clicar no botão de downloads: {str(e)[:200]}")
        return False

def obter_itens_menu(driver):
    """Obtém todos os itens do menu de downloads com seus nomes"""
    try:
        itens = driver.find_elements(By.CSS_SELECTOR, 'ul.p-menu-list li.p-menuitem')
        return [(item, item.find_element(By.CSS_SELECTOR, 'span.p-menuitem-text').text) 
                for item in itens if item.is_displayed()]
    except:
        return []

def processar_downloads(driver, temp_dir, codigo_prg):
    """Processa todos os downloads com múltiplas tentativas"""
    if not abrir_lista_downloads(driver):
        return False

    itens_menu = obter_itens_menu(driver)
    if not itens_menu:
        return False

    resultados = []
    
    for item, nome in itens_menu:
        try:
            def tentar_item(tentativa):
                return tentar_download(driver, nome, temp_dir, codigo_prg, tentativa)
            
            sucesso = tentar_item(1)
            resultados.append((nome, sucesso))
            
        except Exception:
            resultados.append((nome, False))
            
        time.sleep(2)

    return all(status for _, status in resultados)
