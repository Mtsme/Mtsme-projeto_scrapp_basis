Este projeto coleta dados de propostas de pregões eletrônicos do portal ComprasNet, estruturando-os em modelos Pydantic e integrando-se a um sistema de filas RabbitMQ.

## Funcionalidades
- **Web Scraping**: Automação com Selenium para extrair dados de propostas.
- **Conversão de Valores**: Tratamento de valores monetários no formato brasileiro.
- **Estruturação de Dados**: Modelos Pydantic para validação e serialização.
- **Integração com RabbitMQ**: Processamento assíncrono de solicitações de coleta.

## Módulos

### utils.py
- `parse_decimal`: Converte strings monetárias (ex: "R$ 1.234,56") para `Decimal`.

### scraper.py
- Funções de scraping:
  - `coletar_propostas_pregao`: Coordena a navegação e coleta de dados.
  - `_extrair_dados_proposta` e `_extrair_itens_proposta`: Extraem dados de elementos HTML.
  - `obter_motivo_desclassificacao`: Captura motivos de desclassificação.

### models.py
- Modelos de dados:
  - `Proposta`: Dados de uma proposta (CNPJ, valores, situação).
  - `OfertaItem`: Item específico ofertado.
  - `PropostaPregao`: Agrupa todos os dados de um pregão.

### main.py
- Inicia o navegador e executa a coleta. Saída em JSON.

### consume.py
- `Consumer`: Escuta filas RabbitMQ e dispara a coleta ao receber mensagens.

