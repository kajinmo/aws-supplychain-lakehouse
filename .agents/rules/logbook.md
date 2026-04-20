---
trigger: always_on
---

# 📖 Project State & Logbook: Dual-Serving Data Lakehouse

*This document is the Agent's short-term memory. It must be updated at the end of every significant coding task or architectural decision.*

## Status Atual
- **Épico Ativo:** Épico 1 - Fundação da Infraestrutura (Terraform) / Épico 2 - Ingestão e Quality Gate
- **Branch/Feature Atual:** `main` (Setup inicial do projeto)
- **Fase de Desenvolvimento:** Desenho arquitetural concluído. Iniciando a construção prática.

## Change Log & Decisões Arquiteturais
*(Registre aqui as mudanças com a data e o racional técnico)*

- **[2026-04-18] Pivot: Norway Car Sales Dataset:**
  - *Decisão:* Mudança do dataset de E-commerce para Vendas de Carros na Noruega para melhor demonstração de séries temporais por marca.
  - *Decisão:* Redesenho da PK/SK do DynamoDB para `manufacturer` e `year_month`.
  - *Ação:* Refatoração do `kaggle_fetcher.py` para usar a API Nativa (Python SDK) em vez de comandos shell, preparando o terreno para integração com AWS SSM/Secrets Manager.

- **[2026-04-18] Scaffold da Infraestrutura (Terraform):**
  - *Ação:* Criação dos arquivos base do Terraform (`providers.tf`, `variables.tf`, `s3.tf`, `dynamodb.tf`, e `budgets.tf`).
  - *Segurança:* Implementação do `aws_budgets_budget` limitando custos a USD 2.00 e envio de alertas usando configuração `TF_VAR_` via `.env`.
  - *Resiliência:* Adicionada proteção contra exclusão não-intencional (`force_destroy = false`) nos buckets S3 (Bronze, Silver e Quarentena).

- **[2026-04-19] Refatoração do Pipeline de Ingestão Python (Fase B/Qualidade):**
  - *Decisão:* Separação explícita de registros "sãos" e "malformados" (Fail-Fast) antes da Cloud.
  - *Decisão:* Adoção do formato `.parquet` via `pyarrow` para os logs de ingestão visando reduzir custos posteriores e melhorar a integração com Athena.
  - *Ação:* Atualizado `extractor.py` para `ingestion_job.py`, que agora despeja dados aprovados em `data/bronze/` e erros em `data/quarantine/`.
  - *Ação:* Criado um orquestrador CLI (`run_pipeline.py`) que baixa dados da API do Kaggle por padrão, com suporte a injeção de caos local (`--mock`).

- **[2026-04-19] Provisionamento de Infraestrutura e Remote State (Fase A):**
  - *Ação:* Provisionados S3 Buckets (`bronze`, `silver`, `quarantine`), DynamoDB (`operational`) e AWS Budget Alarmes na conta da AWS.
  - *Decisão:* Adotamos o suporte nativo do Terraform 1.10+ para state locking (`use_lockfile = true`), abolindo a necessidade do DynamoDB para state lock.
  - *Ação:* Migração do `terraform.tfstate` de Base-Local concluído integralmente para o S3 Backend Automático.

- **[2026-04-19] Orquestração Serverless (Fase C):**
  - *Decisão:* Substituição do projeto inicial "Airflow isolado no Docker" por uma infraestrutura limpa e orientada a eventos para maximizar uso do Free Tier (Lambda + EventBridge).
  - *Ação:* Provisionada função IAM Least-Privilege e AWS Lambda (`lambda_handler.py`) contendo apenas as regras de negócio em Pydantic. Utilizamos a camada "AWS SDK Pandas" da AWS para importar pacotes pesados como PyArrow sem engordar o build ZIP.
  - *Decisão:* Para contornar a dependência do compilador C/Rust no deploy Windows->Linux da Lambda, realizamos o downgrade intencional dos Data Contracts para o `Pydantic v1`. Ele suporta fallbacks "Pure Python" universais, garantindo a execução Serverless.
  - *Ação:* Provisionado alvo EventBridge agendado mensalmente para invocar a Lambda automaticamente enviando um JSON injetável (`source: mock`).

- **[2026-04-20] Correção de Mapping no Glue (The Split):**
  - *Bug:* Erro `The provided key element does not match the schema` ao gravar no DynamoDB.
  - *Causa:* Descompasso entre nomes de colunas na Bronze (Make, Year, Month) e as chaves esperadas no DynamoDB (manufacturer, year_month).
  - *Ação:* Implementada transformação PySpark usando `withColumn`, `lpad` e `concat` para garantir chaves PK/SK compatíveis com o NoSQL.
  - *Ação:* Scripts atualizados no S3 via `terraform apply` automático.

- **[2026-04-20] Pivot Orquestração Épico 5:**
  - *Decisão:* Mudança de gatilho "Event-Driven S3" por Agendamento Misto (Ingestão de 1h em 1h, Processamento às 19:00 BRT).
  - *Arquitetura (Scale & Save):* Adoção de AWS Step Functions. O fluxo consistirá em: (A) Lambda escala DynamoDB para PROVISIONED -> (B) Glue Job consolida o batch diário no S3/Dynamo -> (C) Lambda retrocede o Banco para PAY_PER_REQUEST.

## Bloqueios / Pontos de Atenção
- RESTRIÇÃO DE ENGENHARIA AWS: Só é permitido alternar o DynamoDB de `Provisioned` para `On-Demand` **uma (1) vez a cada 24 horas**. Essa restrição da AWS se encaixa no batch "Diário", mas nos impede de rodar o ambiente completo no Step Functions várias vezes na mesma tarde.

## Próximos Passos (To-Do)
1. ~~Criar a estrutura inicial de pastas do repositório.~~ *(Concluído)*
2. ~~Desenvolver modelos Pydantic (Car Sales).~~ *(Concluído)*
3. ~~Atualizar scripts de ingestão e extração para o novo dataset.~~ *(Concluído em 2026-04-19)*
4. ~~Iniciar o provisionamento do backend do Terraform (S3 State).~~ *(Concluído)*
5. ~~Configurar alertas de orçamentos (AWS Budgets) via `.env`.~~ *(Concluído)*
6. ~~Desenvolver orquestração da Ingestão na AWS (Evento -> Lambda).~~ *(Concluído)*
7. ~~Desenvolver script AWS Glue para divisão dos dados (Iceberg no Silver e API no DynamoDB).~~ *(Concluído)*
8. Validar a execução completa do Glue Job e observar a ingestão no Console do DynamoDB. *(Concluído)*
9. Criar arquitetura do Épico 5: Lambdas de Scaling do DynamoDB.
10. Criar AWS Step Functions que orquestre Scaling -> Glue -> Descaling.
11. Ajustar Triggers via EventBridge (Cron para 1h mock e 19:00 BRT para o batch).