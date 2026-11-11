---
type: constat::sh-agent-os
genere_par: "[[tache - appliquer la conformite solidai]]"
doc_type: constat
---

# Le gate du sous-agent est vide tant que le démon au-mcp du workspace ne tourne pas

`au daemon status` peut répondre `ready=true` alors que le sous-agent `au-aefi-acquisition` n'a aucun outil.
Ce statut ne parle que du moteur au-engine.
Le gate du sous-agent passe par le démon au-mcp du workspace, qui n'était pas lancé.

**Constat du 2026-11-12.**
- Le serveur MCP `au-aefi-acquisition` du sous-agent annonçait « No tools are available in this session »
- `pgrep -f "au-mcp/src/cli.ts start <ACQ>"` ne rendait rien, alors que les autres repos de la thèse avaient le leur
- Le démon lancé à la main, comme le fait `launch.sh` (`cd ~/arsumbris && node --experimental-strip-types au-mcp/src/cli.ts start <ACQ>`), le gate rend ses 67 outils

**Contournement.**
Les outils d'un sous-agent sont fixés à son lancement : il ne voit pas un démon lancé après lui.
La tâche a donc parlé au gate par un petit client stdio du même serveur (`au-mcp-adapter-cc/bin/mcp-server.ts`, mêmes variables d'environnement que l'agent), avec la session parente pour le hook du registre.
Toutes les écritures sont passées par le gate, sauf le retrait de Packmind, que le skill fait à la main.

**Pour la session qui délègue.**
Avant de déléguer à un `au-<vault>`, vérifie le démon au-mcp du workspace et pas seulement `au daemon status`.
S'il manque, lance-le par le skill `refresh-arsumbris` avant de déléguer.
