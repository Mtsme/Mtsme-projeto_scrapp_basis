from pydantic import BaseModel, field_serializer
from datetime import datetime
from recursos.decisao_e_revisao.revisao_autoridade_competente import revisao_autoridade 
from recursos.decisao_e_revisao.decisao_do_pregoeiro import decisao_pregao
from recursos.decisao_e_revisao.abre_e_clica import inicio, interagir_com_abas 
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import time
import os
import sys
from comum.models import DadosPregao

# Adicione o diretório do projeto ao path se necessário
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class DadosConsolidados(BaseModel):
    id: str
    dados_revisao: list | None = None  
    dados_decisao: list | None = None  
    data_extracao: datetime
    
    @field_serializer('data_extracao')
    def serialize_dt(self, data_extracao: datetime, _info):
        return data_extracao.strftime('%d/%m/%Y %H:%M')

def extrair_dr(driver,dadosprg:DadosPregao,):
    lista_dados_consolidados = []
   
    
    try:
        inicio(dadosprg.codigo_prg,driver)  
        wait = WebDriverWait(driver, timeout=10)

        div_recursos = wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.width-100'))
        )
        num = len(div_recursos)
        
        for i in range(num):
            try:
                div_recursos = wait.until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.width-100')))
                div_recurso = div_recursos[i]

                if div_recurso.is_displayed():
                    try:
                        id_recurso = div_recurso.find_element(By.CSS_SELECTOR, 'span[class="text-uppercase cp-item-bold"]').text.strip()
                        
                        botoes_recurso = wait.until(
                            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'app-botao-icone[class="ng-star-inserted"] button')))
                        if i < len(botoes_recurso):
                            botoes_recurso[i].click()
                            time.sleep(2)

                        interagir_com_abas(driver)
                        time.sleep(1)

                        dados_consolidados = DadosConsolidados(
                            data_extracao=datetime.now(),
                            id=id_recurso,
                            dados_revisao=None,
                            dados_decisao=None
                        )
                        
                        try:
                            dados_consolidados.dados_revisao = revisao_autoridade(driver, id_recurso,dadosprg)
                        except Exception as e:
                            print(f"Erro ao obter revisão da autoridade: {str(e)}")
                        
                        try:
                            dados_consolidados.dados_decisao = decisao_pregao(driver,id_recurso,dadosprg)
                        except Exception as e:
                            print(f"Erro ao obter decisão do pregão: {str(e)}")

                        lista_dados_consolidados.append(dados_consolidados)
                    except Exception as e:
                        print(f"Erro durante a extração de dados do recurso {i}: {str(e)}")
                
                driver.get(f"https://cnetmobile.estaleiro.serpro.gov.br/comprasnet-web/public/compras/acompanhamento-compra?compra={dadosprg.codigo_prg}")
            except Exception as e:
                print(f"Erro ao processar recurso {i}: {str(e)}")
                continue
        
    except Exception as e:
        print(f"Erro geral em extrair_dr: {str(e)}")
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass
            
    return lista_dados_consolidados
