Projeto criado para coletar dados do site Contas.Gov

Arquivo quadro_info -> abre o quadro de informações do site Contas.Gov.

Arquivo coletar_avisos -> usa o Arquivo quadro_info para abrir o quadro de informações e coleta os avisos do mesmo.
Arquivo coletar_impug -> usa o Arquivo quadro_info para abrir o quadro de informações e coleta as impugnações do mesmo.
Arquivo coletar_esclar -> usa o Arquivo quadro_info para abrir o quadro de informações e coleta os esclarecimentos do mesmo.

Arquivo tratam_avisos -> usa o Arquivo coletar_avisos para tratar os dados coletados nesse arquivo, colocando-os em formato json.
Arquivo tratam_impug -> usa o Arquivo coletar_impug para tratar os dados coletados nesse arquivo, colocando-os em formato json.
Arquivo tratam_esclar -> usa o Arquivo coletar_esclar para tratar os dados coletados nesse arquivo, colocando-os em formato json.

Arquivo consumer_avisos -> Adiciona mensageria para coleta de avisos (é referenciado no arquivo tratam_avisos)
Arquivo consumer_impug -> Adiciona mensageria para coleta de impugnações (é referenciado no arquivo tratam_impug)
Arquivo consumer_esclar -> Adiciona mensageria para coleta de esclarecimentos (é referenciado no arquivo tratam_esclar)


├── config.py                 # Configurações de interação com o banco de dados 
