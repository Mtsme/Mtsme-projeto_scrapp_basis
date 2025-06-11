import argparse
import importlib

from loguru import logger

# Mapeia os nomes dos módulos para seus caminhos de importação completos
# Isso permite que o importlib encontre e carregue o módulo dinamicamente.
MODULO_PATHS = {
    'arquivos_compra': 'downloads_compra.main',
    'arquivos_proposta': 'propostas.anexos.main',
    'dados_propostas': 'propostas.dados_gerais.main',
    'status_licitante': 'propostas.status_licitante.main',
    'quadro_informativo': 'quadro_informativo.main',
    'arquivo_recursos': 'recursos.anexos.main',
    'recursos-dados-gerais': 'recursos.dados_gerais.main',
    'decisoes_revisoes': 'recursos.decisao_e_revisao.main',
    'informacoes_pregao': 'info_pregao.main',
    'mensagem_dlq': 'mensagem_dlq.main'
}

HELP = "Módulos disponíveis:"
for k in MODULO_PATHS.keys():
   HELP = HELP + f" {k},"
HELP = HELP[:-1] # Remove a última vírgula

def modulo_nao_encontrado_ou_falha(module_name_arg: str = "", error_msg: str = ""):
    if error_msg:
        logger.error(error_msg)
    else:
        logger.error(f"Módulo '{module_name_arg}' não encontrado ou não possui uma função 'main' válida.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Executar um módulo específico.')
    parser.add_argument('modulo', type=str, help=HELP)
    args = parser.parse_args()

    modulo = args.modulo

    if modulo in MODULO_PATHS:
        
        module_path = MODULO_PATHS[modulo]
        
        # Importa dinamicamente o módulo
        # Somente neste ponto o código do módulo especificado é carregado.
        imported_module = importlib.import_module(module_path)
        
        main_function = getattr(imported_module, 'main', None)
        
        if main_function and callable(main_function):
            logger.info(f"Executando módulo: {modulo}")
            main_function() 
        else:
            modulo_nao_encontrado_ou_falha(modulo, f"Função 'main' não encontrada ou não é chamável no módulo '{modulo}' (path: {module_path}).")
    
    else:
        modulo_nao_encontrado_ou_falha(args.modulo)