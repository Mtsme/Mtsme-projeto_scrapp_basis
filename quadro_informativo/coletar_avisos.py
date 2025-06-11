from selenium.webdriver.common.by import By
from quadro_informativo.quadro_info import abrir_quadro
import time

def coletar_avisos(url,codigo_prg,driver):
    """
    Coleta os dados do quadro informativo (datas e avisos).
    Retorna uma lista de dicionários com os dados coletados.
    """

    try:
         # Abre o quadro informativo
        abrir_quadro(url,driver)
        # Clica na aba de avisos
        btn_impug = driver.find_element(By.XPATH, "/html/body/modal-container/div[2]/div/div/div/app-quadro-informativo/div[2]/p-tabview/div/div[1]/div/ul/li[1]")
        btn_impug.click()
        time.sleep(5)

        # Encontra a div principal que contém todas as datas e avisos
        quadro_informativo = driver.find_element(By.TAG_NAME, "app-informativos")

        # Encontra todas as divs internas que contêm as datas e avisos
        divs_internas = quadro_informativo.find_elements(By.CSS_SELECTOR, "div.row.cp-itens-card.cp-item-expansivel")

        # Lista para armazenar todos os avisos e datas
        avisos = []

        # Itera sobre todas as divs internas
        for div in divs_internas:
            try:
                # Encontra o span com a data dentro da div atual
                data_element = div.find_element(By.CSS_SELECTOR, "span.text-uppercase")
                data_text = data_element.text.strip() 
            except Exception as e:
                # Se não encontrar a data, pula para a próxima div
                print(f"Erro ao localizar a data: {e}")
                continue

            # Encontra o texto do aviso dentro da div atual
            try:
                # O texto do aviso está dentro de um span dentro de div.col-auto.pr-0
                aviso_element = div.find_element(By.CSS_SELECTOR, "div.col-auto.pr-0 span")
                aviso_texto = aviso_element.text.strip()  
            except Exception as e:
                # Se não encontrar o aviso, pula para a próxima div
                print(f"Erro ao localizar o aviso: {e}")
                continue

            # Adiciona os dados à lista
            avisos.append({
                "data": data_text,
                "aviso": aviso_texto,
                "cod_pregao":codigo_prg
            })

        return avisos

    except Exception as e:
        print(f"Erro ao coletar dados: {e}")
        return None
    finally:
        # Fechar o driver do navegador
        driver.quit()
