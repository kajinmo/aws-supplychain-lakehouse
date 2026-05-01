---
trigger: always_on
---

# 📖 Project State & Logbook: Dual-Serving Data Lakehouse

*This document is the Agent's short-term memory. It must be updated at the end of every significant coding task or architectural decision.*

## Change Log & Decisões Arquiteturais
*(Registre aqui as mudanças com a data e o racional técnico)*

- **[2026-04-18] Épico 1: Norway Car Sales Dataset:**
  - *Decisão:* dataset de E-commerce para Vendas de Carros na Noruega para melhor demonstração de séries temporais por marca.
  - *Decisão:* PK/SK do DynamoDB para `manufacturer` e `year_month`.
  - *Ação:* Uso do `kaggle_fetcher.py` para usar a API Nativa (Python SDK) em vez de comandos shell, preparando o terreno para integração com AWS SSM/Secrets Manager.

- **[2026-04-18] Épico 2: Scaffold da Infraestrutura (Terraform):**
  - *Ação:* Criação dos arquivos base do Terraform (`providers.tf`, `variables.tf`, `s3.tf`, `dynamodb.tf`, e `budgets.tf`).
  - *Segurança:* Implementação do `aws_budgets_budget` limitando custos a USD 2.00 e envio de alertas usando configuração `TF_VAR_` via `.env`.
  - *Resiliência:* Adicionada proteção contra exclusão não-intencional (`force_destroy = false`) nos buckets S3 (Bronze, Silver e Quarentena).

- **[2026-04-19] Épico 3: ETL - Refatoração do Pipeline de Ingestão Python (Fase B/Qualidade):**
  - *Decisão:* Separação explícita de registros "sãos" e "malformados" (Fail-Fast) antes da Cloud.
  - *Decisão:* Adoção do formato `.parquet` via `pyarrow` para os logs de ingestão visando reduzir custos posteriores e melhorar a integração com Athena.
  - *Ação:* Atualizado `extractor.py` para `ingestion_job.py`, que agora despeja dados aprovados em `data/bronze/` e erros em `data/quarantine/`.
  - *Ação:* Criado um orquestrador CLI (`run_pipeline.py`) que baixa dados da API do Kaggle por padrão, com suporte a injeção de caos local (`--mock`).

- **[2026-04-19] Épico 3: ETL - Provisionamento de Infraestrutura e Remote State (Fase A):**
  - *Ação:* Provisionados S3 Buckets (`bronze`, `silver`, `quarantine`), DynamoDB (`operational`) e AWS Budget Alarmes na conta da AWS.
  - *Decisão:* Adotamos o suporte nativo do Terraform 1.10+ para state locking (`use_lockfile = true`), abolindo a necessidade do DynamoDB para state lock.
  - *Ação:* Migração do `terraform.tfstate` de Base-Local concluído integralmente para o S3 Backend Automático.

- **[2026-04-19] Épico 3: ETL - Orquestração Serverless (Fase C):**
  - *Decisão:* Substituição do projeto inicial "Airflow isolado no Docker" por uma infraestrutura limpa e orientada a eventos para maximizar uso do Free Tier (Lambda + EventBridge).
  - *Ação:* Provisionada função IAM Least-Privilege e AWS Lambda (`lambda_handler.py`) contendo apenas as regras de negócio em Pydantic. Utilizamos a camada "AWS SDK Pandas" da AWS para importar pacotes pesados como PyArrow sem engordar o build ZIP.
  - *Decisão:* Para contornar a dependência do compilador C/Rust no deploy Windows->Linux da Lambda, realizamos o downgrade intencional dos Data Contracts para o `Pydantic v1`. Ele suporta fallbacks "Pure Python" universais, garantindo a execução Serverless.
  - *Ação:* Provisionado alvo EventBridge agendado mensalmente para invocar a Lambda automaticamente enviando um JSON injetável (`source: mock`).

- **[2026-04-20] Épico 4: Correção de Mapping no Glue (The Split):**
  - *Bug:* Erro `The provided key element does not match the schema` ao gravar no DynamoDB.
  - *Causa:* Descompasso entre nomes de colunas na Bronze (Make, Year, Month) e as chaves esperadas no DynamoDB (manufacturer, year_month).
  - *Ação:* Implementada transformação PySpark usando `withColumn`, `lpad` e `concat` para garantir chaves PK/SK compatíveis com o NoSQL.
  - *Ação:* Scripts atualizados no S3 via `terraform apply` automático.

- **[2026-04-20] Épico 5: Pivot Orquestração:**
  - *Decisão:* Mudança de gatilho "Event-Driven S3" por Agendamento Misto (Ingestão de 1h em 1h, Processamento às 19:00 BRT).
  - *Arquitetura (Scale & Save):* Adoção de AWS Step Functions. O fluxo consistirá em: (A) Lambda escala DynamoDB para PROVISIONED -> (B) Glue Job consolida o batch diário no S3/Dynamo -> (C) Lambda retrocede o Banco para PAY_PER_REQUEST.

- **[2026-04-20] Épico 6: Operational API:**
  - *Decisão:* Uso de API Gateway HTTP API (v2) em vez da REST API clássica. 70% mais barato e menor latência.
  - *Ação:* Criada Lambda `operational_api.py` com rotas `GET /sales` e `GET /sales/{manufacturer}?year=XXXX`.
  - *Ação:* IAM Least Privilege com apenas `dynamodb:Query`, `dynamodb:Scan` e `dynamodb:GetItem`.
  - *Validação:* API testada com sucesso via curl. Endpoint: `https://oforctm94m.execute-api.us-east-1.amazonaws.com`

- **[2026-04-21] Épico 7: Historical Bootstrap & Project Polish (Concluído):**
  - *Decisão:* Alinhamento dos dados Mock para 2017/02 para garantir continuidade lógica com a série histórica do Kaggle (2007-2017).
  - *Ação:* Desenvolvimento e execução do script `historical_bootstrap.py`, resultando na carga de 4.367 registros validados no S3 Bronze.
  - *Ação:* Reorganização do Git histórico por Épicos e modernização do `README.md` (remoção de emojis e adição de diagramas Mermaid).
  - *Ação:* Disparo manual do Step Functions para processamento da carga histórica.

- **[2026-04-21] Épico 8: Frontend Streamlit (Concluído):**
  - *Ação:* Desenvolvido o dashboard completo com 4 páginas (Home, Analytics, Explorer, Health).
  - *Ação:* Implementada integração dual-serving com API Gateway (DynamoDB) e Athena (Gold Layer).
  - *Ação:* Aplicada política de cache (`st.cache_data`) para otimização de custos AWS.
  - *Ação:* Implementada observabilidade da Quarentena (erros Pydantic) no dashboard de saúde.
  - *Validação:* App compilado e estruturado com sucesso.

## Bloqueios / Pontos de Atenção
- RESTRIÇÃO DE ENGENHARIA AWS: Só é permitido alternar o DynamoDB de `Provisioned` para `On-Demand` **uma (1) vez a cada 24 horas**.
- **AVISO DE DEPLOY:** Em novas infraestruturas, os Épicos 6, 7 e 8 não devem ser rodados de maneira automática. Esta parte requer atenção especial e estudo adicional antes da automação total.

## Próximos Passos (Pendências)
- **PROJETO CONCLUÍDO:** Dashboard refatorado com injeção de CSS premium e sistema de cache otimizado implementados em 01/05/2026.
- Acompanhar os logs do AWS Budgets e Monitorar os relatórios mensais.

**PROJETO ENTREGUE COM SUCESSO.**