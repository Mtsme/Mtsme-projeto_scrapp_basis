from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import selenium.webdriver.support.expected_conditions as EC
from propostas.dados_gerais.models import Proposta, PropostaPregao, GrupoPropostas, OfertaItem
from propostas.dados_gerais.utils import parse_decimal
import time
import random
from tenacity import retry, stop_after_attempt, wait_fixed
from propostas.dados_gerais.config_dados import inserir_status_pregao,verificar_ultimo_status
from typing import Optional
from comum.models import DadosPregao


def espera_aleatoria(min=3, max=5):
    """Espera com tempo randomizado para parecer mais humano."""
    time.sleep(random.uniform(min, max))

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def safe_click(driver, element):
    """Tenta clicar no elemento utilizando ActionChains com retry."""
    ActionChains(driver).move_to_element(element).pause(1).click().pause(1).perform()

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def expandir_anexos(driver: WebDriver, botao_anexos):
    """Tenta expandir a seção de anexos com retentativas."""
    try:
        ActionChains(driver).move_to_element(botao_anexos).pause(1).click().pause(1).perform()
        time.sleep(2)  # Espera para carregar
    except Exception as e:
        print(f"Falha ao expandir anexos: {e}")
        raise

# obtem o motivo de desclassificação
def obter_motivo_desclassificacao(elemento, driver: WebDriver):
    wait = WebDriverWait(driver, timeout=10)
    motivo = None
    try:
        # expande o botão de propostas detalhadas
        botao_proposta = elemento.find_element(
            By.XPATH, './/span[contains(., "Proposta")]/ancestor::button'
        )
        ActionChains(driver).click(botao_proposta).perform()
        time.sleep(1.5)

        detalhes_div = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div[class="col-md-12 col-sm-12 col-12 pt-2 ng-star-inserted"]')))
        
        if detalhes_div:
            motivo_elemento= detalhes_div.find_element(By.CSS_SELECTOR, 'div[class="cp-valor-item-08"]')
            motivo = motivo_elemento.text.strip() if "Motivo" in detalhes_div.text else None

    except Exception:
        pass
    return motivo

# extrai os sub-itens de cada propostas
def _extrair_itens_proposta(elemento_proposta, driver: WebDriver) -> list[OfertaItem]:
    items = []
    try:
        botao_expandir = elemento_proposta.find_element(
            By.CSS_SELECTOR, 'app-botao-expandir-ocultar button[data-test="btn-expandir"]'
        )
        ActionChains(driver).click(botao_expandir).perform()
        time.sleep(1)
        
        botao_proposta = elemento_proposta.find_element(
            By.XPATH, './/span[contains(., "Proposta")]/ancestor::button'
        )
        safe_click(driver, botao_proposta)
        time.sleep(3)
        
        pagina_sub_itens = 1
        while True:
            sub_itens = elemento_proposta.find_elements(
                By.CSS_SELECTOR, 'app-card-proposta-subitem-em-selecao-fornecedores'
            )
            if not sub_itens:
                print("Nenhum sub-item encontrado.")
                break
                
                # itera sobre cada sub-item
            for sub_item in sub_itens:
                try:
                    ActionChains(driver).move_to_element(sub_item).perform()
                    botao_expandir_item = sub_item.find_element(
                        By.CSS_SELECTOR, 'app-botao-expandir-item button[data-test="btn-expandir"]'
                    )
                    ActionChains(driver).click(botao_expandir_item).perform()
                    time.sleep(2.5)
                    nome_item = sub_item.find_element(
                        By.XPATH, './/app-identificacao-e-fase-item/div[1]'
                    ).text.split('\n')[0]
                    valores = sub_item.find_element(By.XPATH, './/div[3]').text.split('\n')
                    ofertado = parse_decimal(valores[2])
                    negociado = parse_decimal(valores[3]) if len(valores) > 3 else None
                    items.append(
                        OfertaItem(
                            item=nome_item,
                            valor_ofertado_unit=ofertado,
                            valor_negociado_unit=negociado
                        )
                    )
                except Exception as e:
                    print(f"Erro ao extrair item: {e}")
                    continue

            try:
                # paginaçao se houver muito sub-itens
                listagem_subitens = WebDriverWait(elemento_proposta, 15).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "app-listagem-propostas-subitens-acesso-publico")
                    )
                )
                btn_next_subitem = listagem_subitens.find_element(
                    By.CSS_SELECTOR, "p-paginator button.p-paginator-next"
                )
                if "disabled" in btn_next_subitem.get_attribute("class"):
                    break

                safe_click(driver, btn_next_subitem)
                espera_aleatoria(4, 6)
                pagina_sub_itens += 1
            except Exception as e:
                print(f"Erro na paginação: {e}")
                break

    except Exception as e:
        print(f"Erro ao extrair itens: {e}")
    return items

# extrai dados gerais das propostas
# scraper.py - Alterações na função _extrair_dados_proposta
# scraper.py - Correção na função _extrair_dados_proposta
# scraper.py - Modifique a função _extrair_dados_proposta
def _extrair_dados_proposta(elemento, driver, temp_dir, codigo_prg) -> Optional[Proposta]:
    
    linhas = [linha.strip() for linha in elemento.text.split('\n') if linha.strip()]
    if not linhas or len(linhas) < 3:  # Reduzido para 3 que é o mínimo (CNPJ, Nome, UF)
        return None

    cod_pregao = codigo_prg
    cnpj = linhas[0]
    
    # Verificação mais segura para tipo
    tipo = None
    tipo_keywords = ['ME/EPP', 'Microempresa', 'Pequeno Porte']
    for keyword in tipo_keywords:
        if any(keyword in linha for linha in linhas[1:3]):
            tipo = keyword
            break

    # Navegação mais segura
    nome = linhas[2] if tipo is None else linhas[3]
    
    # Verificação de UF - procura em qualquer linha após o nome
    uf = None
    for linha in linhas[2:]:
        if len(linha) == 2 and linha.isalpha():  # Supõe que UF tem 2 letras
            uf = linha.upper()
            break
    
    if not uf:
        return None
            
    # Verificação de situação
    situacao_candidates = ['Desclassificada', 'Inabilitada', 'Adjudicada', 'Aceita','Aceita e habilitada','Habilitada']
    for candidate in situacao_candidates:
        for candidates in linhas:
            if candidates == candidate:
                situacao=candidate
                break
            
    
    # Valores - pega os últimos 2 campos numéricos
    valores = []
    for linha in reversed(linhas):
        try:
            val = parse_decimal(linha)
            valores.append(val)
            if len(valores) >= 2:
                break
        except:
            continue
    
    ofertado = valores[-1] if valores else None
    negociado = valores[-2] if len(valores) > 1 else None
    
    motivo = obter_motivo_desclassificacao(elemento, driver)

    proposta = Proposta(
        cod_prg=cod_pregao, cnpj=cnpj, tipo=tipo, situacao=situacao if situacao else None,
        nome=nome, uf=uf, ofertado=ofertado,
        negociado=negociado, motivo=motivo, temp_dir=temp_dir
    )

    proposta.oferta_itens = _extrair_itens_proposta(elemento, driver)
    return proposta

# coleta as propostas do pregao
def coletar_propostas_pregao(dadosprg:DadosPregao,driver,temp_dir) -> PropostaPregao:
    pregao = PropostaPregao(codigo_prg=dadosprg.codigo_prg)
    url = f"https://cnetmobile.estaleiro.serpro.gov.br/comprasnet-web/public/compras/acompanhamento-compra?compra={dadosprg.codigo_prg}"
    driver.get(url)

    WebDriverWait(driver, 15).until(
        EC.visibility_of_all_elements_located((By.CSS_SELECTOR, '.background-listagem'))
    )

    # procura se há mais de um grupo por pregao
    botoes = WebDriverWait(driver, 15).until(
        EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, 'app-botao-icone[data-test="acompanhar-item"] button i')
        )
    )

    # itera sobre cada grupo
    for indice in range(len(botoes)):
        botoes = WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, 'app-botao-icone[data-test="acompanhar-item"] button i')
            )
        )
        botoes[indice].click()
        time.sleep(3)

        grupo_element = driver.find_element(
            By.CSS_SELECTOR,
            'div.col-sm-6:nth-child(1) > div:nth-child(1) > app-identificacao-e-fase-item:nth-child(1) > div:nth-child(1) span.text-uppercase:nth-child(2)'
        )
        num_grupo = grupo_element.text.strip() # numero do grupo

        div_propostas = WebDriverWait(driver, 20).until(
            EC.visibility_of_all_elements_located((By.CSS_SELECTOR, 'div.p-dataview-content > div'))
        )

        # adiciona o grupo a proposta
        grupo = GrupoPropostas(num_grupo=num_grupo)
        for elemento_proposta in div_propostas:
            proposta = _extrair_dados_proposta(elemento_proposta, driver, temp_dir, dadosprg.codigo_prg)
            if proposta:

                ultimo=verificar_ultimo_status(
                    cod_pregao=proposta.cod_prg,
                    grupo=grupo.num_grupo,
                    cnpj=proposta.cnpj
                )
                if ultimo != proposta.negociado:

                    inserir_status_pregao(
                        dadosprg=dadosprg.model_dump(),
                        cod_pregao=proposta.cod_prg,
                        grupo=grupo.num_grupo,
                        cnpj=proposta.cnpj,
                        tipo=proposta.tipo,
                        situacao=proposta.situacao,
                        nome=proposta.nome,
                        uf= proposta.uf,
                        ofertado=proposta.ofertado,
                        negociado=proposta.negociado,
                        motivo=proposta.motivo,
                        oferta_itens=proposta.oferta_itens
                    )
                
                
                grupo.propostas.append(proposta)

        pregao.adicionar_grupo(grupo)
        driver.back()
        time.sleep(3)

    return pregao
