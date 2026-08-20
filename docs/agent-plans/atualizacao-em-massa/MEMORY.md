# Memória — Atualização em massa

## Contexto

O painel privado do JobRadar permite alterar a situação de uma vaga por vez.
O pedido é selecionar várias vagas por checkbox e aplicar uma situação única.

## Escopo

- Adicionar seleção por checkbox na lista de vagas.
- Exibir uma barra de ação contextual com quantidade selecionada e situação.
- Criar rota protegida e validada para atualização em massa.
- Cobrir casos de sucesso, seleção vazia e CSRF em testes.
- Publicar por PR, CI e merge.

## Decisões

- A ação em lote reutiliza a mesma lista canônica de situações da atualização individual.
- A seleção é explícita; não haverá “selecionar todas as páginas”, para não alterar vagas fora da lista visível.
- A barra de ações só aparece quando há seleção, para manter o painel enxuto.

## Estado

Interface, rota protegida e testes implementados. A validação local cobre
atualização de múltiplas vagas, seleção vazia e IDs inválidos; CI e preview
da Vercel aprovados, aguardando merge.
