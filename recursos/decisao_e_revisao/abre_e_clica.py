from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import undetected_chromedriver as uc


def inicio(cod_prg, driver):
    driver.get("https://cnetmobile.estaleiro.serpro.gov.br/comprasnet-web/public/compras/acompanhamento-compra?compra="+str(cod_prg))


#função que clica na aba de histórico de recursos
def interagir_com_abas(driver):
    wait = WebDriverWait(driver, timeout=7)
    
    # Clica na aba de detalhes
    try:
        aba_detalhes = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'a.p-tabview-nav-link[data-pc-index="1"]'))
        )
        aba_detalhes.click()
    except TimeoutException:
        print("A aba Histórico de recursos não está disponível.")