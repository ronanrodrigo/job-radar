# Plano — MobileSignal

## Planejamento

Mapear a página pública, seus links de vaga e os campos exibidos. O scraper deve manter a coleta independente de termos, pois a fonte já é específica para iOS.

## Implementação

Criar o módulo em `scrapers/`, extrair cada card para `Job` e registrá-lo em `_SCRAPERS_IOS`.

## Validação

Adicionar testes unitários para a extração e para o perfil. Executar a suíte Python e revisar o diff.

## Publicação

Fazer commit, push, criar PR, aguardar a execução de CI e realizar o merge somente com os checks aprovados.
