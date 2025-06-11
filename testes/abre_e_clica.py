from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc

caminho_download="/home/basis/Downloads"

#essa funçao importa a variavel 'get' de consumer que possui os dados corretos para iterarna url.
def iniciar_driver(get):
    
    print(get)
    options = uc.ChromeOptions()
    options.add_experimental_option("prefs", {
        "download.default_directory": caminho_download,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    })
    driver = uc.Chrome(options=options)
    inicio(get, driver)
    return driver 

#função que inicia a url concatenando a variável get no final
def inicio(get, driver):
    driver.get("https://cnetmobile.estaleiro.serpro.gov.br/comprasnet-web/public/compras/acompanhamento-compra?compra="+str(get))


#função que clica na aba de histórico de recursos
def interagir_com_abas(driver):
    wait = WebDriverWait(driver, timeout=7)
    # Clica na aba de detalhes
    aba_detalhes = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, 'a.p-tabview-nav-link[data-pc-index="1"]'))
    )
    aba_detalhes.click()
    return driver  

if __name__ == "__main__":
    driver = iniciar_driver()
    interagir_com_abas(driver)