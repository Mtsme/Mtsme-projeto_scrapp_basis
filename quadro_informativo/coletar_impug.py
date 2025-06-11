from selenium.webdriver.common.by import By
import time
from quadro_informativo.quadro_info import abrir_quadro

def coletar_impug(url,driver):
    """
    Coleta os dados das impugnações.
    Retorna o texto das impugnações ou None se não houver impugnações.
    """

    try:
        abrir_quadro(url,driver)
        # Clica na aba de impugnações
        btn_impug = driver.find_element(By.XPATH, "/html/body/modal-container/div[2]/div/div/div/app-quadro-informativo/div[2]/p-tabview/div/div[1]/div/ul/li[2]")
        btn_impug.click()
        time.sleep(5)

        # Verifica se existe mensagem de "Nenhum informativo"
        empty_messages = driver.find_elements(By.CSS_SELECTOR, "div.p-dataview-emptymessage")
        if empty_messages and "Nenhum informativo a ser apresentado" in empty_messages[0].text:
            print("Nenhuma impugnação a ser apresentada")
            return ""

        # Extrai o texto completo das impugnações
        impug_element = driver.find_element(By.XPATH, "/html/body/modal-container/div[2]/div/div/div/app-quadro-informativo/div[2]/p-tabview/div/div[2]")
        impug_text = impug_element.text.strip()


        if not impug_text or "Nenhuma impugnação" in impug_text:
            print("Nenhuma impugnação encontrada")
            return ""

        return impug_text

    except Exception as e:
        print(f"Erro ao coletar dados: {e}")
        return None
    finally:
        driver.quit()
