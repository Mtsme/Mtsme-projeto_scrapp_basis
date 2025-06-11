import undetected_chromedriver as uc
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException

TIMEOUT_PADRAO = 10
ESPERA_FIXA_PAGINACAO = 2

def abrir_quadro(url,driver):
    """
    Abre o site e o quadro informativo.
    Retorna o driver configurado.
    """
    driver.get(url)

    try:
        # Espera até o elemento com o botão do quadro informativo aparecer
        WebDriverWait(driver, timeout=TIMEOUT_PADRAO).until(
            EC.presence_of_element_located((By.TAG_NAME, "app-botao-quadro-informativo")),
            "Botão quadro não localizado"
        )

        # Encontra o botão do quadro informativo e clica
        btn_msgs = driver.find_elements(By.CSS_SELECTOR, "app-botao-quadro-informativo i.fa-clipboard")
        for btn in btn_msgs:
            if btn.is_displayed():
                try:
                    btn.click()
                except ElementClickInterceptedException:
                    time.sleep(ESPERA_FIXA_PAGINACAO)
                    btn.click()
                break

        # Aguarda a página carregar completamente
        time.sleep(5)

    except Exception as e:
        print(f"Erro ao abrir o quadro informativo: {e}")
        driver.quit()