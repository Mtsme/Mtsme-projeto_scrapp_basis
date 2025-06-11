import re
from datetime import datetime
from time import sleep

import selenium.webdriver.support.expected_conditions as EC
import undetected_chromedriver as uc
from selenium.common import NoSuchElementException, TimeoutException, ElementClickInterceptedException
from selenium.webdriver.remote.webdriver import By
from selenium.webdriver.support.wait import WebDriverWait
from undetected_chromedriver import WebElement
from loguru import logger

from models import MensagemPregao, DadosMensagemBusca
from utils_chromedriver import suppress_exception_in_del

TIMEOUT_PADRAO = 10
ESPERA_FIXA_PAGINACAO = 2

suppress_exception_in_del(uc)
url_acompanhamento_compras = 'https://cnetmobile.estaleiro.serpro.gov.br/comprasnet-web/public/compras/acompanhamento-compra?compra='


class BuscaMensagens:

    def recupera_mensagens(self, driver, dados_busca: DadosMensagemBusca) -> list[MensagemPregao]:
        mensagens_lidas: list[MensagemPregao] = []
        driver.get(f'{url_acompanhamento_compras}{dados_busca.cod_pregao_pesquisa}')
        WebDriverWait(driver, timeout=TIMEOUT_PADRAO).until(
            EC.presence_of_element_located((By.TAG_NAME, "app-botao-mensagens-da-compra")),
            "Botão mensagens não localizado")
        # Localizar o item a clicar como sendo o ícone, pois ele cobre o centro do botão pai
        btn_msgs = driver.find_elements(By.CSS_SELECTOR, "app-botao-mensagens-da-compra i.fa-envelope")
        for btn in btn_msgs:
            # Procure o primeiro botão visível, tem mais de um por efeito de estilo em caso de rolagem
            if btn.is_displayed():
                try:
                    btn.click()
                # Em alguns casos o ícone com envelope não aparece a tempo em cima do botão
                except ElementClickInterceptedException:
                    logger.debug("Tentando segundo click no botão mensagem")
                    sleep(ESPERA_FIXA_PAGINACAO)
                    btn.click()
                break
        continuar = True
        while continuar:
            WebDriverWait(driver, timeout=TIMEOUT_PADRAO).until(
                EC.presence_of_element_located((By.CLASS_NAME, "cp-mensagens-compra")),
                "Caixas de mensagens não localizadas")
            caixas_mensagens: list[WebElement] = driver.find_elements(By.CLASS_NAME, "cp-mensagens-compra")
            for caixa in caixas_mensagens:
                msg = self.ler_dados_mensagem(caixa)
                if msg.is_mesmo_data_remetente(dados_busca.ultima_mensagem):
                    continuar = False
                    break
                else:
                    mensagens_lidas.insert(0, msg)
            try:
                paginator = WebDriverWait(driver, timeout=TIMEOUT_PADRAO).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR,
                                                    "app-mensagens-da-compra p-dataview p-paginator button[aria-label='Next Page']")))
                # espera antes de clicar para não disparar a trava do captcha
                sleep(ESPERA_FIXA_PAGINACAO)
                paginator.click()
                # espera para atualizar a lista de mensagens
                sleep(ESPERA_FIXA_PAGINACAO)
            except TimeoutException:
                logger.debug('Botão next page não encontrado')
                continuar = False
        return mensagens_lidas

    def ler_dados_mensagem(self, caixa_mensagem: WebElement) -> MensagemPregao:
        return MensagemPregao(
            remetente=self.get_text_element_if_exists(caixa_mensagem, By.CLASS_NAME, "mensagens-remetente"),
            item=self.get_text_element_if_exists(caixa_mensagem, By.CLASS_NAME, "mensagens-item"),
            texto=self.get_text_element_if_exists(caixa_mensagem, By.CLASS_NAME, "mensagens-texto"),
            data_hora=self.get_date_from_message(
                self.get_text_element_if_exists(caixa_mensagem, By.CLASS_NAME, "mensagens-data")))

    def get_date_from_message(self, msg: str) -> datetime | None:
        m = re.search('Enviada em (\d\d/\d\d/\d\d\d\d) às (\d\d:\d\d:\d\d)h', msg)
        retorno = None
        if len(m.groups()) == 2:
            try:
                retorno = datetime.strptime(f'{m.group(1)} {m.group(2)}', '%d/%m/%Y %H:%M:%S')
            except ValueError:
                pass
        return retorno

    def get_text_element_if_exists(self, element: WebElement, by: By, value: str) -> str:
        retorno = ''
        try:
            retorno = element.find_element(by, value).text.strip()
        except NoSuchElementException:
            ...
        return retorno
