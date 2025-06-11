from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from selenium.common.exceptions import TimeoutException
from pydantic import BaseModel
from recursos.decisao_e_revisao.config_dr import inserir_dados_pregao

class Revisao(BaseModel):
    cod_pregao: str
    grupo: str
    secao: str
    nome: str | None = None
    decisao: str
    data_decisao: str
    fundamentacao: str

def revisao_autoridade(driver, id,dadosprg): 
    wait = WebDriverWait(driver, timeout=6)
    todos_dados = []
    
    try:
        elemento = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '.p-dropdown-trigger-icon')))
        elemento.click()
        time.sleep(1)

        qtd_botoes = wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'p-dropdownitem.p-element'))
        ) 
        num = len(qtd_botoes)
        elemento.click()
    except TimeoutException:
        num = 1
    
    for i in range(num):
        j = i + 1
        try:
            elemento = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '.p-dropdown-trigger-icon')))
            elemento.click()
            time.sleep(1)
            troca_sessao = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, f'p-dropdownitem.p-element:nth-child({j})')))
            troca_sessao.click()
            time.sleep(2)

            elemento = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'div.item:nth-child(3) > button:nth-child(1)'))
            )
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", elemento)
            elemento.click()
            time.sleep(3)

            nome_elemento = driver.find_element(
                By.CSS_SELECTOR, 
                'div.item:nth-child(3) > div:nth-child(2) > div:nth-child(1) > app-sessao-revisao-decisao:nth-child(1) > span:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div:nth-child(2)'
            )
            decisao_elemento = driver.find_element(
                By.CSS_SELECTOR, 
                'div.col-sm-3:nth-child(2) > div:nth-child(2)'
            )
            data_elemento = driver.find_element(
                By.CSS_SELECTOR, 
                'div.col-sm-3:nth-child(3) > div:nth-child(2)'
            )
            fundamentacao_elemento = driver.find_element(
                By.CSS_SELECTOR, 
                'div.pt-2:nth-child(4) > div:nth-child(2)'
            )

            dados = Revisao(
                cod_pregao=dadosprg.codigo_prg,
                grupo=id,
                secao=str(j),
                nome=nome_elemento.text.strip(),
                decisao=decisao_elemento.text.strip(),
                data_decisao=data_elemento.text.strip(),
                fundamentacao=fundamentacao_elemento.text.strip()
            )
            inserir_dados_pregao(
                dadospregao=dadosprg.model_dump(),
                cod_pregao=dados.cod_pregao,
                grupo=dados.grupo,
                secao=dados.secao,
                tipo='DECISAO',
                dados={'nome':dados.nome,
                       'decisao': dados.decisao,
                       'data_decisao':dados.data_decisao,
                       'fundamentacao':dados.fundamentacao}
            )
            
            
            todos_dados.append(dados.model_dump())

        except Exception as e:
            print(f"Erro ao interagir com o elemento na sessão {i}: {e}")
            continue
    
    return todos_dados if todos_dados else None
