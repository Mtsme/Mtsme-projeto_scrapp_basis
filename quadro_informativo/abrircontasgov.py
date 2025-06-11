import undetected_chromedriver as uc

def abrir_site(url):
    """
    Abre o site e retorna o driver configurado.
    """
    # Inicializar o driver
    driver = uc.Chrome()
    
    try:
        # Acessar a página
        driver.get(url)
        return driver
    except Exception as e:
        print(f"Erro ao abrir o site: {e}")
        driver.quit()
        return None