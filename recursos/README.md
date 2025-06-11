O programa consiste em coletar os dados de Históricos de recursos no compranet. Segue o passo a passo:
O código inicia no arquivo consumer.py, que importa as mensagens do rabbitmq e extrai os dados necessários para incrementar a url do pregão de interesse.
em seguida a funçoes presente em comsumer importa e executa a função principal de cada aplicação, que está presente em seus respectivos main.py.
Em main.py são importadas e executadas as outras funções do programa, que são:

                1-pregao datas(obter datas):
                    Responsável por obter dados como Datas e numero do pregão.

                2-coleta de dados(extrair dados):
                    Busca e captura em loop, os dados gerais como cnpj, nome da empresa e recursos.
                
                3-decisao do pregoeiro(decisao pregao):
                    Realiza a extração dos dados do fim da página em Decisão do pregoeiro.
                
                4-revisao autoridade competente:
                    realizaa extração dos dados do fim da página em revisao de autoridade competente.

                5-download arquivos(baixar arquivos):
                    busca na página arquivos relevantes dos recurso e realiza o download sempre que possível.

                                                                                                                    '''obs: a lista acima está no seguinte formato: 
                                                                                                                            1-(nomedo arquivo(nome da função))
                                                                                                                                descrição de atuação'''