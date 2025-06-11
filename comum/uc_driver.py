import undetected_chromedriver as uc

def cria_driver(pasta_download='/tmp'):
    options = uc.ChromeOptions()
    # Diretório de download e preferências
    options.add_experimental_option("prefs", {
        "download.default_directory": pasta_download,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    })
    # Adicional: forçar download em alguns casos
    options.add_argument("--enable-features=NetworkService,NetworkServiceInProcess")
    driver = uc.Chrome(options=options)
    return driver