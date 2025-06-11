from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from info_pregao.config import inserir_dados_pregao
from comum.models import DadosPregao
from info_pregao.models import Info


def info_compra(driver,dadosprg:DadosPregao):
    wait = WebDriverWait(driver, timeout=10)
  
    driver.get("https://cnetmobile.estaleiro.serpro.gov.br/comprasnet-web/public/compras/acompanhamento-compra?compra="+str(dadosprg.codigo_prg))
    
    
    
    
    botao = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, 'div.text-right:nth-child(1) > app-botoes-cabecalho-compra:nth-child(1) > span:nth-child(1) > app-botao-detalhamento-compra:nth-child(3) > app-botao-icone:nth-child(1) > span:nth-child(1) > button'))
    )
    
    fase_elemento = driver.find_element(
        By.CSS_SELECTOR,
        'span[class="margem-complemento campo-texto"]'
    )
    modo_elemento = driver.find_element(
        By.CSS_SELECTOR,
        'div.d-inline:nth-child(2) > span'
    )
    criterio_elemento = driver.find_element(
        By.CSS_SELECTOR,
        'div.d-inline:nth-child(1) > span'
    )
    
    botao.click()
    time.sleep(1.5)

    tipo_elemento = driver.find_element(
        By.CSS_SELECTOR,
        '.br-modal-body > div:nth-child(1) > div:nth-child(1) > app-dados-adicionais-compra:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div'
    )
    objeto_elemento = driver.find_element(
        By.CSS_SELECTOR,
        '.text-justify'
    )
    periodo_elemento = driver.find_element(
        By.CSS_SELECTOR,
        '.br-modal-body > div:nth-child(1) > div:nth-child(1) > app-dados-adicionais-compra:nth-child(1) > div:nth-child(3) > div:nth-child(1) > div'
    )
    responsavel_elemento = driver.find_element(
        By.CSS_SELECTOR,
        '.br-modal-body > div:nth-child(1) > div:nth-child(1) > app-dados-adicionais-compra:nth-child(1) > div:nth-child(4) > div:nth-child(1) > div'
    )
    data_elemento = driver.find_element(
        By.CSS_SELECTOR,
        '.br-modal-body > div:nth-child(1) > div:nth-child(1) > app-dados-adicionais-compra:nth-child(1) > div:nth-child(3) > div:nth-child(2) > div'
    )
    uf_elemento = driver.find_element(
        By.CSS_SELECTOR,
        '.br-modal-body > div:nth-child(1) > div:nth-child(1) > app-dados-adicionais-compra:nth-child(1) > div:nth-child(4) > div:nth-child(2) > div'
    )
    id_elemento = driver.find_element(
        By.CSS_SELECTOR,
        'div.row:nth-child(5) > div:nth-child(1) > div'
    )

    dados_info = Info(
        fase_contratacao=fase_elemento.text.strip(),
        modo_disputa=modo_elemento.text.strip(),
        criterio_julgamento=criterio_elemento.text.strip(),
        cod_prg=dadosprg.codigo_prg,
        tipo_objeto=tipo_elemento.text.strip(),
        objeto=objeto_elemento.text.strip(),
        periodo_entrega=periodo_elemento.text.strip(),
        responsavel_compra=responsavel_elemento.text.strip(),
        data_abertura=data_elemento.text.strip(),
        uf_uasg=uf_elemento.text.strip(),
        id_pncp= id_elemento.text.strip()
    )
  
    
    inserir_dados_pregao(dados_info,dadosprg)

            
    

