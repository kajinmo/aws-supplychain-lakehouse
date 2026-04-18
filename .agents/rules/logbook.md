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

## Bloqueios / Pontos de Atenção
- Configurar o AWS Budget Alert na conta da AWS antes de provisionar qualquer recurso via Terraform para garantir o limite de custos (Free Tier).

## Próximos Passos (To-Do)
1. ~~Criar a estrutura inicial de pastas do repositório.~~ *(Concluído)*
2. ~~Desenvolver modelos Pydantic (Car Sales).~~ *(Concluído)*
3. Atualizar scripts de ingestão e extração para o novo dataset.
4. Iniciar o provisionamento do backend do Terraform (State Lock / S3 e DynamoDB).
5. Configurar alertas de orçamentos (AWS Budgets).