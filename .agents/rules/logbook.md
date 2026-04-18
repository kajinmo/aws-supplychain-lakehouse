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

- **[2026-04-18] Inicialização do Projeto & Definição de Arquitetura:**
  - *Decisão:* Adoção de arquitetura Serverless (Glue, Athena, DynamoDB, Lambda, S3) focada no Free Tier da AWS.
  - *Decisão:* Implementação de um "Quality Gate" com Pydantic na camada Bronze (Fail-Fast) para evitar custos de processamento no Glue com dados malformados.
  - *Decisão:* Modelagem do DynamoDB definida com PK=`customer_id` e SK=`date` para otimizar o padrão de acesso do histórico de compras.

- **[2026-04-18] Scaffold do Projeto & Contratos Pydantic:**
  - *Ação:* Criação da estrutura de pastas base (`infra/terraform`, `src/extract`, `src/models`, `src/transform`, `src/api`, `frontend`, `dags`, `tests`).
  - *Decisão:* Definição dos modelos Pydantic `AnalyticalOrder` (Bronze Layer fail-fast) e `ApplicationOrder` (Operational Layer API). Validação estrita para evitar chaves nulas ou vazias.

## Bloqueios / Pontos de Atenção
- Configurar o AWS Budget Alert na conta da AWS antes de provisionar qualquer recurso via Terraform para garantir o limite de custos (Free Tier).

## Próximos Passos (To-Do)
1. ~~Criar a estrutura inicial de pastas do repositório (`infra/`, `src/`, `tests/`, etc.).~~ *(Concluído)*
2. ~~Desenvolver os modelos de validação de dados usando `pydantic` com base no E-commerce Sales Dataset do Kaggle.~~ *(Concluído)*
3. Iniciar o provisionamento do backend do Terraform (State Lock / S3 e DynamoDB).
4. Configurar alertas de orçamentos (AWS Budgets) via Terraform para garantir monitoramento do Free Tier.