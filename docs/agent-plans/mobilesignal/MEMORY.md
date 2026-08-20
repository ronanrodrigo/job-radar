# Memória — MobileSignal

## Contexto

Adicionar `mobilesignal.io/latest-jobs` às fontes do perfil iOS. A fonte lista exclusivamente vagas iOS, com título, empresa, data, modalidade, localização e uma página própria por vaga.

## Escopo

- Criar um scraper isolado para a listagem MobileSignal.
- Integrá-lo ao perfil iOS na frequência alta.
- Cobrir a extração e o registro do scraper com testes determinísticos.
- Abrir PR, aguardar o CI e fazer merge após os checks verdes.

## Decisões

- O scraper será infraestrutura (`scrapers/`) e entregará `Job`, preservando o desenho atual do projeto.
- A página é uma listagem única; ela será consultada uma vez por ciclo, sem repetir a mesma coleta para cada termo.
- A fonte contém vagas remotas, híbridas e presenciais norte-americanas. O filtro iOS existente mantém apenas os locais/remotos compatíveis com o perfil.

## Estado

Scraper implementado e validado localmente contra a página pública: 20 cards
foram extraídos. A suíte local passou com 363 testes e o CI do PR passou;
aguardando merge.
