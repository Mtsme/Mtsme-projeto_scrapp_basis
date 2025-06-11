import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def coletar_identificacao_compra(driver):
    """
    Coleta apenas o texto bruto do elemento app-identificacao-compra
    """
    elemento = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "app-identificacao-compra"))
    )
    return elemento.text


def coletar_pregao_orgao(codigo_compra: str, driver) -> str | None:
    """
    Função principal para coleta dos dados brutos
    """
    url = f"https://cnetmobile.estaleiro.serpro.gov.br/comprasnet-web/public/compras/acompanhamento-compra?compra={codigo_compra}"
    
    driver.get(url)

    time.sleep(2)  # Espera para carregamento
    identificacao_compra = coletar_identificacao_compra(driver)
    return identificacao_compra
