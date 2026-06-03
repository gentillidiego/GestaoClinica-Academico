# Guia de Contribuição

Este repositório contém dados e fluxos clínicos sensíveis. Mudanças devem ser pequenas, revisáveis e acompanhadas de validação objetiva.

## Fluxo Recomendado

1. Crie uma branch a partir de `main`.
2. Entenda o fluxo afetado antes de alterar.
3. Faça mudanças focadas.
4. Rode validações locais.
5. Atualize documentação quando a mudança alterar uso, deploy, banco, segurança, permissões, PDFs ou comportamento visível.
6. Abra pull request com resumo, impacto e validações executadas.

## Checklist de Pull Request

- [ ] A alteração está limitada ao escopo do problema.
- [ ] Não há segredos, bancos, logs, PDFs temporários ou dumps versionados.
- [ ] Queries usam placeholders `%s`.
- [ ] Fluxos com permissão clínica foram testados com perfis compatíveis.
- [ ] PDFs afetados foram gerados e revisados.
- [ ] Documentação foi atualizada quando necessário.
- [ ] `python3 -m compileall app.py blueprints services tasks scripts` foi executado.

## Padrões Técnicos

- Não introduza ORM sem decisão técnica explícita.
- Não use SQLite como fonte oficial de dados.
- Não altere regras clínicas assinadas sem revisar bloqueios de edição e auditoria.
- Não reduza validações de professor, aluno executor ou paciente.
- Não faça `git add -A` em worktree misto sem revisar o diff.

## Segurança

Credenciais devem vir do ambiente. Use `.env.example` apenas como modelo sem valores reais.

Antes de compartilhar o repositório, confirme:

- `.env` não está versionado.
- `clinica.db`, backups e dumps não estão versionados.
- `logs/`, `pdf_temp/`, cookies e arquivos de teste de carga não estão versionados.
- A branch publicada não contém dados pessoais de pacientes.
