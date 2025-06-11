from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from datetime import datetime
from selenium.webdriver.support.ui import WebDriverWait
import selenium.webdriver.support.expected_conditions as EC
import time
from quadro_informativo.quadro_info import abrir_quadro

class Esclarecimento:
    def __init__(self, data, questionamento, resposta, codigo_prg):
        self.data = data
        self.questionamento = questionamento
        self.resposta = resposta
        self.codigo_prg = codigo_prg

def coletar_esclarecimentos(url, codigo_prg,driver):
    """
    Coleta os esclarecimentos a partir do quadro informativo.
    Retorna uma lista de objetos Esclarecimento.
    """

    try:
        abrir_quadro(url,driver)
        # Clica na aba de esclarecimentos
        btn_esclarec = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "/html/body/modal-container/div[2]/div/div/div/app-quadro-informativo/div[2]/p-tabview/div/div[1]/div/ul/li[3]"))
        )
        btn_esclarec.click()

        # Espera o conteúdo dos esclarecimentos ser carregado
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "/html/body/modal-container/div[2]/div/div/div/app-quadro-informativo/div[2]/p-tabview/div/div[2]/p-tabpanel[3]/div/app-informativos/div/p-dataview/div/div")),
            "Esclarecimentos não carregaram corretamente"
        )

        time.sleep(5)  # Aguarda mais tempo para garantir carregamento

        esclarecimentos_elements = driver.find_elements(By.CSS_SELECTOR, "div.row.cp-itens-card.cp-item-expansivel")
        esclarecimentos = []

        for elem in esclarecimentos_elements:
            try:
                # Extrai as datas
                data_elements = elem.find_elements(By.CSS_SELECTOR, "div.content.p-0 div.subtitle span.text-uppercase")
                if not data_elements:
                    continue

                data_text = data_elements[0].text.strip()
                if not data_text:
                    continue

                try:
                    data_convertida = datetime.strptime(data_text, "%d/%m/%Y %H:%M")
                except ValueError:
                    print(f"Formato de data inválido: {data_text}")
                    continue

                # Extrai o questionamento
                questionamento_element = elem.find_element(By.CSS_SELECTOR, "div.col-md-11")
                questionamento_texto = questionamento_element.text.strip()

                # Extrai a resposta
                resposta_element = elem.find_element(By.CSS_SELECTOR, "div.content.pr-0.ng-star-inserted")
                resposta_texto = resposta_element.text.strip()

                if data_text and questionamento_texto and resposta_texto:
                    esclarecimentos.append(Esclarecimento(
                        data=data_convertida,
                        questionamento=questionamento_texto,
                        resposta=resposta_texto,
                        codigo_prg=codigo_prg
                    ))

            except NoSuchElementException as e:
                print(f"Elemento não encontrado: {e}")
            except Exception as e:
                print(f"Erro ao extrair informações: {e}")

        return esclarecimentos

    except Exception as e:
        print(f"Erro durante a coleta de esclarecimentos: {e}")
        return []
    finally:
        driver.quit()