# Plano — Atualização em massa

## Planejamento

Manter a seleção limitada à lista atualmente renderizada e reutilizar os estados
existentes para não introduzir valores fora do fluxo de candidatura.

## Implementação

Adicionar checkboxes por vaga, uma barra de ação que informa a quantidade
selecionada e uma rota `POST` que valida CSRF, IDs e situação antes de
persistir cada alteração.

## Validação

Cobrir o endpoint e a renderização da interface com testes determinísticos;
executar a suíte completa e inspecionar a interface em preview.

## Publicação

Criar PR, aguardar todos os checks e fazer merge após aprovação.
