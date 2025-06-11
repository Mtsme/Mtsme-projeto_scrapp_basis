from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from pydantic import BaseModel
from typing import List
from quadro_informativo.abrircontasgov import abrir_site

class LicitacaoInfo(BaseModel):
    fase_contratacao: str
    criterio_julgamento: str
    modo_disputa: str

class LicitacoesInfo(BaseModel):
    licitacoes: List[LicitacaoInfo]

def limpar_texto(texto, prefixo):
    return texto.replace(prefixo, "").strip()

def coletar_dados(driver):
    """
    Coleta os dados da página e os trata.
    Retorna uma lista de objetos LicitacaoInfo.
    """
    try:
        criteriojulg_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.d-inline.pr-4.ng-star-inserted"))
        )
        criteriojulg_texto = limpar_texto(criteriojulg_element.text.strip(), "Critério julgamento:")

        mododisputa_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.d-inline.ng-star-inserted:not(.pr-4)"))
        )
        mododisputa_texto = limpar_texto(mododisputa_element.text.strip(), "Modo disputa:")

        status_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "span.margem-complemento.campo-texto"))
        )
        status_texto = status_element.text.strip()

        return [LicitacaoInfo(
            fase_contratacao=status_texto,
            criterio_julgamento=criteriojulg_texto,
            modo_disputa=mododisputa_texto
        )]

    except TimeoutException as e:
        print(f"Erro ao coletar dados: {e}")
        return []
    finally:
        driver.quit()

def main(codigo_prg: str):
    """
    Função principal padronizada que recebe o código do pregão
    e retorna as informações da licitação em JSON.
    """
    url = f"https://cnetmobile.estaleiro.serpro.gov.br/comprasnet-web/public/compras/acompanhamento-compra?compra={codigo_prg}"
    
    driver = abrir_site(url)
    
    if driver:
        lista_dados = coletar_dados(driver)
        if lista_dados:
            resultado = LicitacoesInfo(licitacoes=lista_dados).model_dump_json(indent=2)
            print(resultado)

'''if __name__ == "__main__":
    main("15397805900062024") '''